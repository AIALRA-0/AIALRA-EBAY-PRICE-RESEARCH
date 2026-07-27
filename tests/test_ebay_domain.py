from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "ebay-price-research"
sys.path.insert(0, str(SKILL / "scripts"))

from merge_rounds import build_shortlist  # noqa: E402
from rank_offers import ranked_output  # noqa: E402
from validate_access import validate as validate_access  # noqa: E402
from validate_final import validate as validate_final  # noqa: E402
from validate_inspection import validate as validate_inspection  # noqa: E402
from validate_plan import validate as validate_plan  # noqa: E402
from validate_round_results import validate as validate_round_results  # noqa: E402


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat()


def source() -> dict:
    return {
        "request_text": "搜索 eBay VITURE Beast XR glasses 最便宜可行商品",
        "marketplace": "ebay.com",
        "destination_country": "United States",
        "destination_region": "California",
        "comparison_currency": "USD",
        "desired_condition": "any",
        "buying_formats": ["fixed-price", "best-offer"],
        "detail_limit": 6,
    }


def plan() -> dict:
    return {
        "request_text": source()["request_text"],
        "product": {
            "canonical_query": "VITURE Beast XR glasses",
            "category": "XR glasses",
            "condition": "any",
            "required_terms": ["VITURE", "Beast"],
            "excluded_terms": ["case only", "lens only", "parts only"],
        },
        "purchase_context": {
            "marketplace": "ebay.com",
            "destination_country": "United States",
            "destination_region": "California",
            "comparison_currency": "USD",
        },
        "constraints": {
            "maximum_budget": "unknown",
            "allowed_buying_formats": ["fixed-price", "best-offer"],
            "allow_unknown_shipping": True,
            "require_returns": False,
        },
        "collection": {
            "query_variants": [
                "VITURE Beast XR glasses",
                "VITURE The Beast smart glasses",
                "VITURE Beast AR glasses",
            ],
            "sort_modes": ["best-match", "price-plus-shipping-ascending", "newly-listed"],
            "minimum_rounds": 3,
            "maximum_rounds": 6,
            "pages_per_round": 1,
            "candidate_limit": 80,
            "detail_limit": 6,
            "saturation": {"min_new_unique_per_round": 1, "consecutive_rounds": 2},
            "pacing": {"maximum_parallel_pages": 2, "minimum_action_interval_seconds": 1.5},
        },
        "assumptions": ["未提供预算"],
    }


def access() -> dict:
    return {
        "plan": plan(),
        "access": {
            "source_backend": "supported-browser",
            "marketplace": "ebay.com",
            "search_transition_verified": True,
            "visible_state": "results-visible",
            "login_state": "anonymous",
            "checked_at": now_iso(),
        },
    }


def card(cid: str, iid: str, rid: str, query: str, title: str, price: str, rank: int, sort: str) -> dict:
    return {
        "candidate_id": cid,
        "platform_item_id": iid,
        "round_id": rid,
        "query": query,
        "sort_mode": sort,
        "source_backend": "supported-browser",
        "page_number": 1,
        "result_rank": rank,
        "title": title,
        "displayed_price": price,
        "currency": "USD",
        "buying_formats": ["fixed-price", "best-offer"],
        "condition_summary": "Certified Refurbished",
        "seller_name": f"seller-{iid}",
        "shipping_text": "Free shipping",
        "image_url": "https://i.ebayimg.com/images/g/example/s-l1600.webp",
        "url": f"https://www.ebay.com/itm/example-title/{iid}?hash=tracking",
        "retrieved_at": now_iso(),
    }


def rounds(access_payload: dict | None = None) -> dict:
    access_payload = access_payload or access()
    p = access_payload["plan"]
    queries = p["collection"]["query_variants"]
    round_rows = [
        {"round_id": "round-1", "query": queries[0], "sort_mode": "best-match", "source_backend": "supported-browser", "page_numbers": [1], "retrieved_at": now_iso(), "result_count": 3},
        {"round_id": "round-2", "query": queries[1], "sort_mode": "price-plus-shipping-ascending", "source_backend": "supported-browser", "page_numbers": [1], "retrieved_at": now_iso(), "result_count": 2},
        {"round_id": "round-3", "query": queries[2], "sort_mode": "newly-listed", "source_backend": "supported-browser", "page_numbers": [1], "retrieved_at": now_iso(), "result_count": 2},
    ]
    cards = [
        card("c1", "366447553040", "round-1", queries[0], "VITURE The Beast XR Glasses Certified Refurbished", "443.32", 1, "best-match"),
        card("c2", "357755551111", "round-1", queries[0], "VITURE Beast Smart XR Glasses", "450.00", 2, "best-match"),
        card("c3", "256447553042", "round-1", queries[0], "VITURE Beast case only", "20.00", 3, "best-match"),
        card("c4", "366447553040", "round-2", queries[1], "VITURE The Beast XR Glasses Certified Refurbished", "443.32", 2, "price-plus-shipping-ascending"),
        card("c5", "336447553043", "round-2", queries[1], "VITURE The Beast AR Smart Glasses", "468.21", 1, "price-plus-shipping-ascending"),
        card("c6", "366447553040", "round-3", queries[2], "VITURE The Beast XR Glasses Certified Refurbished", "443.32", 3, "newly-listed"),
        card("c7", "336447553043", "round-3", queries[2], "VITURE The Beast AR Smart Glasses", "468.21", 2, "newly-listed"),
    ]
    return {
        "plan": p,
        "access": access_payload["access"],
        "collection_status": {"stop_reason": "saturated", "blocked_reasons": []},
        "rounds": round_rows,
        "candidates": cards,
    }


def offer(item: dict, price: str, *, risk: bool = False, scope: str = "public", formats: list[str] | None = None, currency: str = "USD") -> dict:
    return {
        "offer_id": item["candidate_id"],
        "platform_item_id": item["platform_item_id"],
        "title": item["title"],
        "url": item["url"],
        "image_urls": [item["image_url"]],
        "search_backends": item["source_backends"],
        "detail_backend": "supported-browser",
        "listing_type": "product",
        "listing_state": "active",
        "buying_formats": formats or ["fixed-price", "best-offer"],
        "match_confidence": "high",
        "match_reasons": ["品牌和型号一致"],
        "condition": "certified-refurbished",
        "selected_variant": "Beast XR glasses",
        "availability": "in-stock",
        "price": price,
        "shipping": "0",
        "import_charges": "0",
        "tax": "0",
        "discount": "0",
        "discount_verified": False,
        "currency": currency,
        "price_scope": scope,
        "seller": {
            "name": item["seller_name"],
            "feedback_percent": "96.0" if risk else "99.9",
            "feedback_count": "20" if risk else "12785",
            "top_rated": not risk,
        },
        "policy": {"returns": "not-accepted" if risk else "accepted", "returns_window": "30 days", "warranty": "Two-year warranty"},
        "reviews": {"inspected": True, "rating": "4.8", "rating_count": "124", "negative_themes": ["white flicker"] if risk else []},
        "signals": {"quantity_available": "3", "sold_count": "47", "negative_signals": [], "contradictions": ["shipping conflict"] if risk else []},
        "evidence_level": "A",
        "retrieved_at": now_iso(),
        "seen_in_rounds": item["seen_in_rounds"],
        "rank_history": item["rank_history"],
    }


def inspection(shortlist: dict, offers: list[dict]) -> dict:
    return {
        "plan": shortlist["plan"],
        "access": shortlist["access"],
        "round_coverage": shortlist["round_coverage"],
        "inspection_coverage": {
            "details_attempted": len(offers),
            "details_verified": len(offers),
            "reviews_inspected": len(offers),
            "failed_urls": [],
        },
        "offers": offers,
    }


class EbayDomainTests(unittest.TestCase):
    def test_plan_and_access_contracts(self) -> None:
        self.assertEqual([], validate_plan(source(), plan()))
        duplicate = plan()
        duplicate["collection"]["query_variants"][1] = duplicate["collection"]["query_variants"][0]
        self.assertTrue(validate_plan(source(), duplicate))
        a = access()
        self.assertEqual([], validate_access(a["plan"], a))
        a["access"]["search_transition_verified"] = False
        self.assertTrue(validate_access(a["plan"], a))

    def test_round_merge_deduplicates_and_removes_accessory(self) -> None:
        payload = rounds()
        a = {"plan": payload["plan"], "access": payload["access"]}
        self.assertEqual([], validate_round_results(a, payload))
        result = build_shortlist(payload)
        self.assertEqual([3, 1, 0], result["round_coverage"]["new_unique_by_round"])
        self.assertEqual(3, result["round_coverage"]["duplicate_observations"])
        self.assertEqual(["round-1", "round-2", "round-3"], result["shortlist"][0]["seen_in_rounds"])
        self.assertNotIn("256447553042", {row["platform_item_id"] for row in result["shortlist"]})

    def test_backend_change_and_false_saturation_are_rejected(self) -> None:
        payload = rounds()
        payload["rounds"][1]["source_backend"] = "trusted-ebay-mcp"
        a = {"plan": payload["plan"], "access": payload["access"]}
        self.assertTrue(validate_round_results(a, payload))
        payload = rounds()
        q = payload["rounds"][2]["query"]
        payload["candidates"].extend([
            card("c8", "346447553044", "round-3", q, "VITURE Beast XR Glasses", "480", 4, "newly-listed"),
            card("c9", "356447553045", "round-3", q, "VITURE Beast XR Glasses", "490", 5, "newly-listed"),
        ])
        payload["rounds"][2]["result_count"] += 2
        a = {"plan": payload["plan"], "access": payload["access"]}
        self.assertTrue(validate_round_results(a, payload))

    def test_ranking_chooses_lowest_viable_complete_total(self) -> None:
        shortlist = build_shortlist(rounds())
        offers = [offer(shortlist["shortlist"][0], "443.32"), offer(shortlist["shortlist"][1], "450", risk=True)]
        data = inspection(shortlist, offers)
        self.assertEqual([], validate_inspection(shortlist, data))
        result = ranked_output(data)
        self.assertEqual(offers[0]["offer_id"], result["recommendation"]["winner_id"])
        self.assertEqual([], validate_final(result))

    def test_auction_and_mixed_currency_cannot_win(self) -> None:
        shortlist = build_shortlist(rounds())
        auction = offer(shortlist["shortlist"][0], "100", scope="current-bid", formats=["auction"])
        foreign = offer(shortlist["shortlist"][1], "300", currency="EUR")
        result = ranked_output(inspection(shortlist, [auction, foreign]))
        self.assertEqual("no-result", result["status"])
        self.assertEqual([], validate_final(result))

    def test_empty_visible_result_completes(self) -> None:
        a = access()
        a["access"]["visible_state"] = "no-results-visible"
        payload = rounds(a)
        payload["candidates"] = []
        for row in payload["rounds"]:
            row["result_count"] = 0
        shortlist = build_shortlist(payload)
        data = inspection(shortlist, [])
        self.assertEqual([], validate_inspection(shortlist, data))
        self.assertEqual("no-result", ranked_output(data)["status"])

    def test_workflow_is_read_only_and_audited(self) -> None:
        workflow = json.loads((SKILL / "workflow.yaml").read_text(encoding="utf-8"))
        self.assertLessEqual({node["side_effect"] for node in workflow["execution"]["graph"]["nodes"]}, {"none", "read"})
        routing = workflow["execution"]["graph"]["nodes"][1]["action"]["arguments"]["source_routing"]
        self.assertEqual(["official-ebay-api", "trusted-ebay-mcp", "supported-browser"], routing["provider_order"])
        text = (SKILL / "references" / "backend-routing.md").read_text(encoding="utf-8")
        self.assertIn("CooKey-Monster/EbayMcpServer", text)
        self.assertIn("拒绝", text)


class EbayRunnerEndToEndTests(unittest.TestCase):
    def run_runner(self, *arguments: str) -> dict:
        completed = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "runner.py"), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)
        return json.loads(completed.stdout)

    def test_runner_completes_full_graph(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)

            def write(name: str, value: dict) -> str:
                path = directory / name
                path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
                return str(path)

            started = self.run_runner("start", "--input", write("input.json", source()))
            sid = started["state_id"]
            self.run_runner("advance", "--state-id", sid)
            self.run_runner("submit", "--state-id", sid, "--node-id", "plan-research", "--output", write("plan.json", plan()))
            self.run_runner("advance", "--state-id", sid)
            a = access()
            self.run_runner("submit", "--state-id", sid, "--node-id", "preflight-access", "--output", write("access.json", a))
            self.run_runner("advance", "--state-id", sid)
            round_payload = rounds(a)
            self.run_runner("submit", "--state-id", sid, "--node-id", "collect-search-rounds", "--output", write("rounds.json", round_payload))
            directive = self.run_runner("advance", "--state-id", sid)
            self.assertEqual("inspect-details", directive["node"]["id"])
            shortlist = build_shortlist(round_payload)
            offers = [offer(shortlist["shortlist"][0], "443.32"), offer(shortlist["shortlist"][1], "450", risk=True)]
            data = inspection(shortlist, offers)
            self.run_runner("submit", "--state-id", sid, "--node-id", "inspect-details", "--output", write("inspection.json", data))
            completed = self.run_runner("advance", "--state-id", sid)
            self.assertEqual("completed", completed["status"])
            self.assertEqual(offers[0]["offer_id"], completed["final_output"]["recommendation"]["winner_id"])


if __name__ == "__main__":
    unittest.main()
