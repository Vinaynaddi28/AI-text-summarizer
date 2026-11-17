from fastapi import APIRouter, HTTPException, Response

from app.models.history import HistoryEntry
from app.services.history import clear_history, delete_summary, get_summary, list_summaries

router = APIRouter(prefix="/api/history")


@router.get("", response_model=list[HistoryEntry])
def history():
    return list_summaries()


@router.get("/{summary_id}", response_model=HistoryEntry)
def history_entry(summary_id: int):
    entry = get_summary(summary_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found.")
    return entry


@router.delete("/{summary_id}", status_code=204)
def delete_history_entry(summary_id: int):
    if not delete_summary(summary_id):
        raise HTTPException(status_code=404, detail="History entry not found.")
    return Response(status_code=204)


@router.delete("", status_code=204)
def delete_all_history():
    clear_history()
    return Response(status_code=204)
