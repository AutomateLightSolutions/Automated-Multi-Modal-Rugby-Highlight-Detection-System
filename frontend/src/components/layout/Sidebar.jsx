import { Search, Plus, Trash2, AlertTriangle } from "lucide-react";
import { useState } from "react";
import PropTypes from "prop-types";
import StatusBadge from "../ui/StatusBadge";
import { formatTimeAgo } from "../../utils/formatters";

export default function Sidebar({
  matches,
  selectedId,
  onSelect,
  onUploadClick,
  deleteIds,
  onToggleDelete,
  onDeleteConfirm,
  deleteLoading,
}) {
  const [query, setQuery] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const filtered = matches.filter((m) =>
    m.filename.toLowerCase().includes(query.toLowerCase()),
  );

  const deleteCount = deleteIds.size;

  const handleDeleteClick = () => {
    if (confirmDelete) {
      onDeleteConfirm();
      setConfirmDelete(false);
    } else {
      setConfirmDelete(true);
    }
  };

  const handleCancelDelete = () => {
    setConfirmDelete(false);
  };

  return (
    <aside className="w-[280px] shrink-0 flex flex-col gap-4 h-[calc(100vh-4rem)] sticky top-16">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-text-primary">Matches</h2>
        {matches.length > 0 && (
          <span className="badge-indigo">{matches.length}</span>
        )}
      </div>

      <div className="relative">
        <Search
          size={14}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
        />
        <input
          className="input pl-9 py-2 text-sm"
          placeholder="Search matches…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 px-1">
        {filtered.length === 0 && (
          <p className="text-sm text-text-muted text-center py-8">
            No matches yet
          </p>
        )}
        {filtered.map((m) => {
          const isChecked = deleteIds.has(m.match_id);
          let itemCls =
            "border-border bg-bg-card hover:border-border-light hover:bg-bg-hover";
          if (isChecked) itemCls = "border-red-500/40 bg-red-500/5";
          else if (selectedId === m.match_id)
            itemCls = "border-accent-indigo bg-indigo-500/5 border-l-2";

          return (
            <div key={m.match_id} className="group flex items-center gap-2">
              <input
                type="checkbox"
                checked={isChecked}
                onChange={() => onToggleDelete(m.match_id)}
                onClick={(e) => e.stopPropagation()}
                className={`shrink-0 w-4 h-4 rounded border-border bg-bg-tertiary
                            accent-red-500 cursor-pointer transition-opacity
                            ${isChecked || deleteIds.size > 0 ? "opacity-100" : "opacity-0 group-hover:opacity-100"}`}
              />
              <button
                onClick={() => onSelect(m.match_id)}
                className={`flex-1 text-left p-3 rounded-xl border transition-all duration-200 ${itemCls}`}
              >
                <p className="text-sm font-medium text-text-primary break-all line-clamp-2 leading-snug">
                  {m.filename}
                </p>
                <div className="flex items-center gap-2 mt-1.5">
                  <StatusBadge status={m.status} />
                  <span className="text-xs text-text-muted">
                    {formatTimeAgo(m.uploadedAt)}
                  </span>
                </div>
              </button>
            </div>
          );
        })}
      </div>

      {deleteCount > 0 && (
        <div className="space-y-2">
          {confirmDelete ? (
            <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-3 space-y-2">
              <div className="flex items-center gap-1.5 justify-center text-red-400">
                <AlertTriangle size={13} />
                <p className="text-xs font-medium">
                  Delete {deleteCount} match{deleteCount > 1 ? "es" : ""}{" "}
                  permanently?
                </p>
              </div>
              <p className="text-[11px] text-text-muted text-center">
                All chunks, audio and highlight files will be removed.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={handleCancelDelete}
                  className="btn-ghost flex-1 text-xs py-1.5"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteClick}
                  disabled={deleteLoading}
                  className="flex-1 text-xs py-1.5 bg-red-500/20 border border-red-500/40
                             text-red-400 rounded-lg hover:bg-red-500/30 transition-colors
                             disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deleteLoading ? "Deleting…" : "Yes, delete"}
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={handleDeleteClick}
              className="w-full flex items-center justify-center gap-2 text-sm py-2
                         bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl
                         hover:bg-red-500/20 transition-colors"
            >
              <Trash2 size={14} />
              Delete {deleteCount} selected
            </button>
          )}
        </div>
      )}

      <button
        className="btn-primary w-full flex items-center justify-center gap-2"
        onClick={onUploadClick}
      >
        <Plus size={16} />
        Upload New
      </button>
    </aside>
  );
}

Sidebar.propTypes = {
  matches: PropTypes.array.isRequired,
  selectedId: PropTypes.string,
  onSelect: PropTypes.func.isRequired,
  onUploadClick: PropTypes.func.isRequired,
  deleteIds: PropTypes.instanceOf(Set).isRequired,
  onToggleDelete: PropTypes.func.isRequired,
  onDeleteConfirm: PropTypes.func.isRequired,
  deleteLoading: PropTypes.bool,
};
