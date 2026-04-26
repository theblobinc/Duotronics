from __future__ import annotations

import torch

from .cell import WGRNNCell
from .policy import WGRNNPolicy
from .records import MemoryUpdateRecord
from .sample_data import SAMPLE_EVENTS, embedding_for_event, witness_from_event


def build_sample_cell() -> WGRNNCell:
    torch.manual_seed(17)
    cell = WGRNNCell(
        input_dim=4,
        hidden_dim=4,
        cell_dim=4,
        slot_dim=4,
        num_slots=4,
        bank_id="sample-research-bank",
    )
    with torch.no_grad():
        cell.memory_bank.content_matrix[0] = torch.tensor([0.02, 0.01, 0.00, 0.03])
        cell.memory_bank.content_matrix[1] = torch.tensor([0.01, 0.03, 0.02, 0.00])
    return cell


def run_sample_loop(*, return_records: bool = False) -> list[MemoryUpdateRecord]:
    cell = build_sample_cell()
    policy = WGRNNPolicy()
    h = torch.zeros(cell.hidden_dim)
    c = torch.zeros(cell.cell_dim)
    records: list[MemoryUpdateRecord] = []
    for index, event in enumerate(SAMPLE_EVENTS):
        witness = witness_from_event(event)
        x_t = embedding_for_event(index, cell.input_dim)
        h, c, record = cell(x_t, h, c, witness, policy)
        records.append(record)
        if not return_records:
            print(
                "event={event_id} update_kind={kind} authority={authority:.2f} affected_slots={slots}".format(
                    event_id=event["id"],
                    kind=record.update_kind,
                    authority=record.authority_t,
                    slots=record.affected_slot_ids,
                )
            )
    return records


def main() -> None:
    run_sample_loop(return_records=False)


if __name__ == "__main__":
    main()
