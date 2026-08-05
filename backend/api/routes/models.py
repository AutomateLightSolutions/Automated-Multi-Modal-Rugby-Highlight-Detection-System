"""
Model management routes: upload a trained model (zip) — and, for the
commentary module, a lexicon.json — into backend/weights/<module>/, and
report what's currently installed per module. Local admin tool — no auth,
matching api/routes/admin.py.

Model weights are pure filesystem artifacts (no DB tracking), consistent
with how modules/visual/inference.py already reads backend/weights/visual/best_model.pt.
"""
import json
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.schemas import ModelStatusResponse, ModelUploadResponse, ModuleModelStatus
from config import settings

router = APIRouter()

MODULES = ("visual", "audio_energy", "commentary")

# Filenames a commentary checkpoint directory may contain — used to (a) find
# the checkpoint root inside an uploaded zip and (b) know which existing
# files to replace without touching the sibling "lexicon/" subdirectory.
_CHECKPOINT_FILENAMES = (
    "config.json", "pytorch_model.bin", "model.safetensors",
    "tokenizer.json", "tokenizer_config.json", "vocab.json", "vocab.txt",
    "merges.txt", "special_tokens_map.json",
)
_REQUIRED_CHECKPOINT_FILES = ("config.json", "tokenizer_config.json")
_CHECKPOINT_WEIGHT_FILES = ("pytorch_model.bin", "model.safetensors")


def _weights_dir(module: str) -> Path:
    return Path(settings.MODEL_WEIGHTS_PATH) / module


def _safe_extract(zf: zipfile.ZipFile, dest_dir: Path) -> None:
    """Extract a zip, rejecting any member whose resolved path escapes dest_dir (zip-slip)."""
    dest_dir = dest_dir.resolve()
    for member in zf.infolist():
        target = (dest_dir / member.filename).resolve()
        if dest_dir != target and dest_dir not in target.parents:
            raise HTTPException(status_code=400, detail=f"Unsafe path in zip: {member.filename}")
    zf.extractall(dest_dir)


def _find_checkpoint_root(extract_dir: Path) -> Path:
    """A checkpoint may be zipped at the archive root or inside one nested
    folder (e.g. 'best/config.json'). Locate whichever directory directly
    contains config.json."""
    if (extract_dir / "config.json").exists():
        return extract_dir

    candidates = [p for p in extract_dir.iterdir() if p.is_dir() and (p / "config.json").exists()]
    if len(candidates) == 1:
        return candidates[0]

    raise HTTPException(
        status_code=400,
        detail="Could not locate a checkpoint (config.json) in the uploaded zip.",
    )


async def _stream_upload_to(file: UploadFile, dest_path: Path) -> int:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    async with aiofiles.open(dest_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            total_bytes += len(chunk)
            await out.write(chunk)
    return total_bytes


def _install_commentary_checkpoint(checkpoint_root: Path, model_dir: Path) -> dict:
    missing = [f for f in _REQUIRED_CHECKPOINT_FILES if not (checkpoint_root / f).exists()]
    if missing:
        raise HTTPException(status_code=400, detail=f"Checkpoint is missing required file(s): {missing}")
    if not any((checkpoint_root / f).exists() for f in _CHECKPOINT_WEIGHT_FILES):
        raise HTTPException(
            status_code=400,
            detail="Checkpoint is missing model weights (model.safetensors or pytorch_model.bin).",
        )

    config = json.loads((checkpoint_root / "config.json").read_text(encoding="utf-8"))

    model_dir.mkdir(parents=True, exist_ok=True)
    for name in _CHECKPOINT_FILENAMES:
        old = model_dir / name
        if old.exists():
            old.unlink()

    copied = []
    for item in checkpoint_root.iterdir():
        if item.is_file():
            shutil.copy2(item, model_dir / item.name)
            copied.append(item.name)

    return {
        "model_type": config.get("model_type"),
        "num_labels": len(config.get("id2label", {})) or None,
        "files": copied,
    }


def _install_generic_model(extract_dir: Path, model_dir: Path) -> list[str]:
    """Best-effort install for modules other than commentary: dump the
    zip's contents into weights/<module>/, replacing what's there."""
    model_dir.mkdir(parents=True, exist_ok=True)
    for item in model_dir.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item, ignore_errors=True)

    installed = []
    for item in extract_dir.iterdir():
        target = model_dir / item.name
        if item.is_file():
            shutil.copy2(item, target)
        else:
            shutil.copytree(item, target)
        installed.append(item.name)
    return installed


@router.post("/admin/models/upload", response_model=ModelUploadResponse)
async def upload_model(
    module: str = Form(...),
    model_file: UploadFile = File(...),
    lexicon_file: Optional[UploadFile] = File(None),
):
    if module not in MODULES:
        raise HTTPException(status_code=400, detail=f"Unknown module '{module}'. Must be one of {MODULES}.")
    if not model_file.filename or Path(model_file.filename).suffix.lower() != ".zip":
        raise HTTPException(status_code=400, detail="Model file must be a .zip archive.")
    if module == "commentary" and lexicon_file is None:
        raise HTTPException(status_code=400, detail="A lexicon.json file is required for the commentary module.")
    if module != "commentary" and lexicon_file is not None:
        raise HTTPException(status_code=400, detail="A lexicon file is only accepted for the commentary module.")

    model_dir = _weights_dir(module)
    tmp_root = model_dir / f"_upload_tmp_{uuid.uuid4().hex}"
    zip_path = tmp_root / "upload.zip"

    try:
        total_bytes = await _stream_upload_to(model_file, zip_path)
        if total_bytes == 0:
            raise HTTPException(status_code=400, detail="Uploaded model file is empty.")

        extract_dir = tmp_root / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                _safe_extract(zf, extract_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Uploaded model file is not a valid zip archive.")

        if module == "commentary":
            checkpoint_root = _find_checkpoint_root(extract_dir)
            config_summary = _install_commentary_checkpoint(checkpoint_root, model_dir)
        else:
            config_summary = {"files": _install_generic_model(extract_dir, model_dir)}

        meta = {
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "original_filename": model_file.filename,
            "size_bytes": total_bytes,
            "config_summary": config_summary,
        }
        (model_dir / "model_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        lexicon_installed = None
        if lexicon_file is not None:
            lexicon_installed = await _install_lexicon(lexicon_file, model_dir)

        return ModelUploadResponse(
            module=module,
            model_installed=True,
            lexicon_installed=lexicon_installed,
            message=f"Model installed for module '{module}'.",
        )
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


async def _install_lexicon(lexicon_file: UploadFile, model_dir: Path) -> bool:
    if not lexicon_file.filename or Path(lexicon_file.filename).suffix.lower() != ".json":
        raise HTTPException(status_code=400, detail="Lexicon file must be a .json file.")

    raw = await lexicon_file.read()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Lexicon file is not valid JSON.")

    if not isinstance(parsed, dict) or not isinstance(parsed.get("categories"), list):
        raise HTTPException(
            status_code=400,
            detail="Lexicon JSON must be an object with a top-level 'categories' list.",
        )

    lexicon_dir = model_dir / "lexicon"
    lexicon_dir.mkdir(parents=True, exist_ok=True)
    (lexicon_dir / "lexicon.json").write_text(json.dumps(parsed, indent=2), encoding="utf-8")

    meta = {
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "original_filename": lexicon_file.filename,
        "categories_count": len(parsed["categories"]),
    }
    (lexicon_dir / "lexicon_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return True


def _read_meta(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


@router.get("/admin/models/status", response_model=ModelStatusResponse)
async def get_models_status():
    modules_status = {}
    for module in MODULES:
        model_dir = _weights_dir(module)
        meta = _read_meta(model_dir / "model_meta.json")

        if module == "commentary":
            model_installed = all(
                (model_dir / f).exists() for f in _REQUIRED_CHECKPOINT_FILES
            ) and any((model_dir / f).exists() for f in _CHECKPOINT_WEIGHT_FILES)
        else:
            model_installed = model_dir.is_dir() and any(
                p.name != ".gitkeep" and not p.name.startswith("_upload_tmp")
                for p in model_dir.iterdir()
            )

        status_kwargs = {
            "model_installed": model_installed,
            "uploaded_at": meta.get("uploaded_at"),
            "original_filename": meta.get("original_filename"),
        }

        if module == "commentary":
            lexicon_meta = _read_meta(model_dir / "lexicon" / "lexicon_meta.json")
            status_kwargs["lexicon_installed"] = (model_dir / "lexicon" / "lexicon.json").exists()
            status_kwargs["lexicon_uploaded_at"] = lexicon_meta.get("uploaded_at")
            status_kwargs["lexicon_original_filename"] = lexicon_meta.get("original_filename")

        modules_status[module] = ModuleModelStatus(**status_kwargs)

    return ModelStatusResponse(modules=modules_status)
