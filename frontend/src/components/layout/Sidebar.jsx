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
  onDeleteMatch,
  deleteLoading,
}) {
  const [query, setQuery] = useState("");
  const [pendingDeleteId, setPendingDeleteId] = useState(null);

  const filtered = matches.filter((m) =>
    m.filename.toLowerCase().includes(query.toLowerCase()),
  );

  const handleTrashClick = (e, matchId) => {
    e.stopPropagation();
    setPendingDeleteId(matchId);
  };

  const handleConfirm = async () => {
    await onDeleteMatch(pendingDeleteId);
    setPendingDeleteId(null);
  };

  const handleCancel = () => setPendingDeleteId(null);

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
          const isSelected = selectedId === m.match_id;
          const isPending = pendingDeleteId === m.match_id;

          return (
            <div key={m.match_id} className="space-y-1.5">
              <div className="group flex items-center gap-2">
                <button
                  onClick={() => onSelect(m.match_id)}
                  className={`flex-1 text-left p-3 rounded-xl border transition-all duration-200
                    ${isPending
                      ? "border-red-500/40 bg-red-500/5"
                      : isSelected
                        ? "border-accent-indigo bg-indigo-500/5 border-l-2"
                        : "border-border bg-bg-card hover:border-border-light hover:bg-bg-hover"
                    }`}
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

                <button
                  onClick={(e) => handleTrashClick(e, m.match_id)}
                  title="Delete match"
                  className="shrink-0 p-1.5 rounded-lg text-text-muted hover:text-red-400
                             hover:bg-red-500/10 opacity-0 group-hover:opacity-100
                             transition-all duration-150"
                >
                  <Trash2 size={14} />
                </button>
              </div>

              {isPending && (
                <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-3 space-y-2">
                  <div className="flex items-center gap-1.5 text-red-400">
                    <AlertTriangle size={13} />
                    <p className="text-xs font-medium">Delete permanently?</p>
                  </div>
                  <p className="text-[11px] text-text-muted leading-relaxed">
                    All raw video, audio, and chunk files will be removed from storage.
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={handleCancel}
                      disabled={deleteLoading}
                      className="btn-ghost flex-1 text-xs py-1.5 disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleConfirm}
                      disabled={deleteLoading}
                      className="flex-1 text-xs py-1.5 bg-red-500/20 border border-red-500/40
                                 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors
                                 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {deleteLoading ? "Deleting…" : "Yes, delete"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

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
  onDeleteMatch: PropTypes.func.isRequired,
  deleteLoading: PropTypes.bool,
};
