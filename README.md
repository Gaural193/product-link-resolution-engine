# Weekly Deals Link Resolution Pipeline

This project is a backend enrichment tool designed to take weekly deal rows without links and resolve them to real retailer product pages, making them ready for marketing email pipelines.

## Setup Instructions

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   Rename `.env.example` to `.env` and add your [SerpApi](https://serpapi.com/) key.
   ```env
   SERPAPI_KEY=your_api_key_here
   ```
4. **Initialize Database**:
   ```bash
   python src/cli.py setup-db
   ```
5. **Run the Pipeline**:
   ```bash
   python src/cli.py enrich-links data/sample-deals.json data/enriched-deals.json
   ```
6. **Generate HTML Preview**:
   ```bash
   python src/cli.py generate-preview data/enriched-deals.json data/preview.html "CVS"
   ```

## Tooling Decisions

- **Typer**: Used for building the CLI. It makes it incredibly fast to generate professional, documented command-line interfaces.
- **SQLAlchemy & SQLite**: Used for local caching and data persistence. Provides a lightweight, structured way to prevent duplicate API calls and trace resolution history without the overhead of spinning up a Postgres container for local testing.
- **RapidFuzz**: Chosen for fuzzy string matching (`token_set_ratio`). Retailers often alter product titles (e.g., adding brand names or adjectives like "Frozen"). `token_set_ratio` handles subset matches and out-of-order words beautifully, preventing artificial score degradation.
- **SerpApi**: Used as the primary search mechanism. It accurately mimics human Google searches constrained by specific retailer domains.

## Matching & Resolution Logic

1. **Database Check**: The pipeline checks the SQLite database to see if the exact `(retailer, product)` combination has already been successfully resolved in a previous run.
2. **Search Query**: If no cache exists, it queries SerpApi. We enforce domain specificity using the `site:retailer.com` operator whenever we know the retailer's actual domain.
3. **Scoring**: `RapidFuzz` computes a similarity score out of 100.
4. **Evaluation**:
   - `Score >= 85`: High confidence exact match.
   - `Score >= 70`: Acceptable near match.
   - `Score < 70`: Low confidence match (Marked as Unresolved).
5. **URL Validation**: Basic validation ensures we don't accidentally link users to a retailer's search page instead of a direct product page.

## Tradeoffs

- **Speed vs. Accuracy**: We rely on SerpApi which is highly accurate but introduces a network delay (~1.5s per unresolved row). We trade raw processing speed for search engine-level accuracy.
- **SQLite vs. PostgreSQL**: SQLite is used for ease of setup. In a true production environment running concurrently on cloud workers, a migration to PostgreSQL is necessary to handle concurrent writes safely.

---

## Scale & Cost Strategy

**1. How would you avoid re-linking the same products every week?**
The pipeline utilizes an SQLite database. Before every API call, it queries the `deal_link_results` table. If the product was already successfully resolved with high confidence, it skips the search step and immediately pulls the cached URL.

**2. What keys would you use for caching and reuse?**
The composite key used for caching is the combination of `retailer` and `original_product`. Because sizes can sometimes fluctuate in data entry, tying the cache strictly to the retailer and product name ensures maximum cache hit rates while maintaining accuracy.

**3. When would you trust an old link vs refresh it?**
Product URLs on massive retail sites (Walmart, CVS) rarely change for core inventory items. An old link can be trusted indefinitely *unless* a metric tracking system (like SendGrid click-tracking) reports a 404 error, at which point the cache for that item should be invalidated and refreshed on the next run. For seasonal items, a cache expiration of 6 months could be implemented.

**4. How would you handle multiple retailers at scale?**
The modular design allows for retailer-specific resolvers. While SerpApi handles most retailers generically via the `site:` operator, at high scale, it would be cost-effective to swap the generic `resolver.py` with custom API clients for retailers that offer public product APIs (like Walmart's affiliate API), falling back to SerpApi only for retailers without public endpoints.

**5. How would you keep this cheap enough to run weekly across thousands of email rows?**
By batching database commits, enforcing strict caching, and normalizing product names before caching. Most weekly grocery emails feature repeating staples (milk, chicken, standard detergents). The cache hit rate would likely exceed 80% after the first month, meaning only 20% of rows require paid API calls.

**6. How would you measure link quality and failures over time?**
By aggregating the `status` and `resolution_method` columns from the `deal_link_results` database table. An automated weekly dashboard could query this table to flag if the "Unresolved" percentage jumps above a certain threshold (e.g., 5%), triggering an alert to investigate whether a retailer changed their URL structure or domain.

---

## Third-Party Tools (SerpApi) Explanation

**When is it used?**
It is used only when a product is completely new to the system and does not exist in the local database cache.

**How much might it cost?**
SerpApi costs $50/month for 5,000 searches, or $130/month for 15,000 searches. At scale, assuming 10,000 *unique* new products per month, it would cost approximately $130/month. 

**Why would you use it in a weekly production workflow?**
Building and maintaining custom web scrapers for 8+ different massive retailers is a full-time engineering job due to anti-bot protections (Cloudflare, Datadome) and frequent DOM changes. Paying $130/month for SerpApi completely outsources the scraper maintenance, proxy rotation, and CAPTCHA solving, making it significantly cheaper than engineering salaries.
