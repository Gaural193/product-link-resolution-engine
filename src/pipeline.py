from db import SessionLocal, DealLinkRun, DealLinkResult
from resolver import resolve_product_link
from matcher import calculate_confidence, evaluate_match

class PipelineManager:
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.db = SessionLocal()

    def run(self, data: list[dict]) -> list[dict]:
        # 1. Create a new run record
        run = DealLinkRun(source_name=self.source_name)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        enriched_data = []

        for row in data:
            retailer = row.get("retailer")
            product = row.get("product")
            size = row.get("size")
            
            # Enriched fields that will be added to the row
            resolved_product_name = None
            resolved_product_url = None
            confidence_score = 0.0
            resolution_method = "Unresolved"
            status = "unresolved"
            notes = ""

            # 2. Check Cache
            cached_result = self.db.query(DealLinkResult).filter(
                DealLinkResult.retailer == retailer,
                DealLinkResult.original_product == product,
                DealLinkResult.status == "resolved"
            ).first()

            if cached_result:
                # Use Cached Result
                resolved_product_name = cached_result.resolved_product_name
                resolved_product_url = cached_result.resolved_product_url
                confidence_score = cached_result.confidence_score
                resolution_method = "Cached"
                status = "resolved"
                notes = "Loaded from cache"
            else:
                # 3. Use Search API
                search_title, search_url = resolve_product_link(retailer, product, size)
                
                if search_title and search_url:
                    # 4. Evaluate the match
                    score = calculate_confidence(product, size, search_title)
                    status, notes = evaluate_match(score, url=search_url)
                    
                    resolved_product_name = search_title
                    resolved_product_url = search_url
                    confidence_score = score
                    resolution_method = "Search API"
                else:
                    notes = "No search results found or error"

            # 5. Save the result to the DB
            db_result = DealLinkResult(
                run_id=run.id,
                retailer=retailer,
                original_product=product,
                original_size=size,
                resolved_product_name=resolved_product_name,
                resolved_product_url=resolved_product_url,
                confidence_score=confidence_score,
                resolution_method=resolution_method,
                status=status,
                notes=notes
            )
            self.db.add(db_result)
            self.db.commit()

            # 6. Append to the enriched output
            enriched_row = row.copy()
            enriched_row.update({
                "resolved_product_name": resolved_product_name,
                "resolved_product_url": resolved_product_url,
                "confidence_score": confidence_score,
                "resolution_method": resolution_method,
                "status": status,
                "notes": notes
            })
            enriched_data.append(enriched_row)
            
            print(f"Processed: {product} -> {status} (Score: {confidence_score})")

        self.db.close()
        return enriched_data
