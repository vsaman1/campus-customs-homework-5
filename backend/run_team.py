from __future__ import annotations

import argparse
import asyncio

from .models import TicketRunRequest
from .team import CampusCustomsTeam


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Campus Customs agent team for one ticket.")
    parser.add_argument("ticket_id", type=int)
    parser.add_argument("request")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    result = await CampusCustomsTeam().run_ticket(TicketRunRequest(ticket_id=args.ticket_id, request=args.request))
    print(result)


if __name__ == "__main__":
    asyncio.run(main())