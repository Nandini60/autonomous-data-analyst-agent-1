"""
Sample Business Document Generator
====================================
Generates 3 realistic business PDF documents for the RAG pipeline:
  1. Q1 2024 Market Analysis Report
  2. Product Return Policy Document
  3. Sales Strategy Memo for 2024

Uses fpdf2 to create properly formatted multi-page PDFs.

Usage:
    python utils/generate_docs.py              # writes to data/docs/
    python utils/generate_docs.py --outdir data/docs
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fpdf import FPDF


# ---------------------------------------------------------------------------
# PDF helper
# ---------------------------------------------------------------------------

class BusinessPDF(FPDF):
    """Custom PDF class with consistent business document styling."""

    def __init__(self, title: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._doc_title = title
        self.set_auto_page_break(auto=True, margin=20)

    def header(self) -> None:
        """Render page header with title and line."""
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, self._doc_title, align="L")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self) -> None:
        """Render page footer with page number."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_section_title(self, title: str) -> None:
        """Add a bold section heading."""
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 30, 30)
        self.ln(4)
        self.cell(0, 10, title)
        self.ln(10)

    def add_subsection_title(self, title: str) -> None:
        """Add a bold subsection heading."""
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(50, 50, 50)
        self.ln(2)
        self.cell(0, 8, title)
        self.ln(8)

    def add_body_text(self, text: str) -> None:
        """Add body paragraph text with proper formatting."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def add_cover_page(self, title: str, subtitle: str, date: str, author: str) -> None:
        """Add a professional cover page."""
        self.add_page()
        self.ln(60)
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(30, 30, 100)
        self.cell(0, 15, title, align="C")
        self.ln(20)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, subtitle, align="C")
        self.ln(30)
        self.set_font("Helvetica", "", 11)
        self.cell(0, 8, f"Prepared by: {author}", align="C")
        self.ln(8)
        self.cell(0, 8, f"Date: {date}", align="C")
        self.ln(8)
        self.cell(0, 8, "Classification: Internal - Confidential", align="C")


# ---------------------------------------------------------------------------
# Document 1: Q1 Market Analysis Report
# ---------------------------------------------------------------------------

def _create_market_analysis(outdir: Path) -> Path:
    """Generate Q1 2024 Market Analysis Report PDF."""
    pdf = BusinessPDF("Q1 2024 Market Analysis Report")
    pdf.alias_nb_pages()

    pdf.add_cover_page(
        title="Q1 2024 Market Analysis Report",
        subtitle="Quarterly Performance Review & Market Insights",
        date="April 15, 2024",
        author="Strategic Analytics Division",
    )

    # Executive Summary
    pdf.add_page()
    pdf.add_section_title("1. Executive Summary")
    pdf.add_body_text(
        "The first quarter of 2024 demonstrated robust growth across all three product "
        "categories, with total revenue reaching $4.2 million, representing a 12.3% "
        "year-over-year increase. Technology products led the growth at 18.7%, driven "
        "primarily by strong enterprise laptop sales and the new iPhone 15 Pro lineup. "
        "Furniture category showed moderate growth at 8.2%, while Office Supplies "
        "maintained steady performance with 6.1% growth."
    )
    pdf.add_body_text(
        "The East region emerged as the top-performing geography, contributing 31% of "
        "total revenue ($1.302 million), followed by the West region at 28%. The Central "
        "and South regions contributed 22% and 19% respectively. Consumer segment remains "
        "our largest customer base at 52% of orders, though Corporate segment showed the "
        "fastest growth rate at 15.4% year-over-year."
    )
    pdf.add_body_text(
        "Key concern: profit margins in the Furniture category declined by 2.1 percentage "
        "points due to increased shipping costs and aggressive discounting on chairs. "
        "The average discount rate increased from 12% to 15.3% in Q1, which directly "
        "impacted bottom-line profitability. We recommend implementing a maximum discount "
        "cap of 20% for all furniture items effective Q2 2024."
    )

    # Market Overview
    pdf.add_section_title("2. Market Overview")
    pdf.add_subsection_title("2.1 Industry Trends")
    pdf.add_body_text(
        "The US office products and technology market grew 7.8% in Q1 2024, outpacing "
        "the broader retail sector growth of 4.2%. Remote and hybrid work arrangements "
        "continue to drive demand for home office equipment, with ergonomic chairs and "
        "standing desks seeing 22% increased demand. The commercial furniture market is "
        "expected to reach $48.2 billion by end of 2024."
    )
    pdf.add_body_text(
        "Technology spending showed resilience despite macroeconomic uncertainty. "
        "Enterprise IT budgets increased by an average of 5.3% year-over-year, with "
        "particular strength in laptop and monitor purchases as companies refresh aging "
        "fleet devices. The shift toward USB-C standardization drove a 34% increase in "
        "accessory sales, particularly hubs, docks, and adapters."
    )

    pdf.add_subsection_title("2.2 Competitive Landscape")
    pdf.add_body_text(
        "Our primary competitors - Staples Business Advantage and Office Depot Pro - "
        "both reported flat to slightly negative growth in Q1. Our market share in the "
        "mid-market segment (companies with 50-500 employees) increased from 14.2% to "
        "15.8%, primarily driven by our enhanced same-day delivery capabilities in "
        "metropolitan areas. Customer satisfaction scores averaged 4.3/5.0, up from "
        "4.1/5.0 in the previous quarter."
    )
    pdf.add_body_text(
        "Amazon Business remains a significant competitive threat in the Office Supplies "
        "category, particularly for consumables like paper and binders. However, our "
        "value-added services (bulk customization, dedicated account management, and "
        "net-30 payment terms) continue to differentiate us in the Corporate segment. "
        "Customer retention rate for Corporate accounts stands at 91.3%."
    )

    # Revenue Analysis
    pdf.add_section_title("3. Revenue Analysis by Category")
    pdf.add_subsection_title("3.1 Technology ($1.89M, +18.7% YoY)")
    pdf.add_body_text(
        "Technology was the standout performer in Q1 2024. Laptop sales contributed "
        "$980,000 (51.9% of tech revenue), with the Dell XPS 15 and Lenovo ThinkPad "
        "X1 Carbon being the best sellers. Phone sales reached $520,000, boosted by "
        "corporate bulk orders for the Apple iPhone 15 Pro. Accessories generated "
        "$390,000, with the Samsung 27-inch 4K Monitor emerging as a surprise hit "
        "at $128,000 in sales alone."
    )
    pdf.add_body_text(
        "Technology profit margins averaged 22.4%, the highest across all categories. "
        "The accessories sub-category had the best margin at 31.2%, while phones had "
        "the lowest at 14.8% due to competitive pricing pressure. We successfully "
        "maintained our premium positioning on laptops with an average selling price "
        "of $1,687, compared to the industry average of $1,420."
    )

    pdf.add_subsection_title("3.2 Furniture ($1.26M, +8.2% YoY)")
    pdf.add_body_text(
        "Furniture revenue was driven by the continued work-from-home trend. Chairs "
        "accounted for 52% of furniture revenue ($655,200), with the Herman Miller "
        "Aeron and Steelcase Leap V2 being premium bestsellers. Tables contributed "
        "33% ($415,800), led by the Autonomous SmartDesk Pro standing desk which "
        "saw a 45% increase in orders compared to Q4 2023."
    )
    pdf.add_body_text(
        "Bookcases showed declining demand (-3.2% YoY), reflecting the broader trend "
        "toward digital document storage. We recommend reducing bookcase inventory by "
        "15% and reallocating warehouse space to accommodate the growing demand for "
        "ergonomic furniture. The average order value for furniture was $487, up from "
        "$452 in Q1 2023. However, profit margins were compressed to 8.6% due to "
        "rising logistics costs and a higher return rate of 11.2% on furniture items."
    )

    pdf.add_subsection_title("3.3 Office Supplies ($1.05M, +6.1% YoY)")
    pdf.add_body_text(
        "Office Supplies maintained steady growth with paper products contributing "
        "$378,000 (36%), storage solutions at $315,000 (30%), binders at $210,000 "
        "(20%), and art supplies at $147,000 (14%). The shift toward premium paper "
        "products (Southworth 25% Cotton Paper) drove a 2.3 percentage point increase "
        "in category profit margins to 18.7%."
    )
    pdf.add_body_text(
        "Seasonal demand patterns were consistent with historical trends, with January "
        "being the strongest month (38% of Q1 supply revenue) as businesses restocked "
        "after year-end budget resets. The subscription-based auto-replenishment program "
        "launched in February contributed $52,000 in recurring revenue with a 94% "
        "retention rate after 60 days."
    )

    # Regional Performance
    pdf.add_section_title("4. Regional Performance")
    pdf.add_body_text(
        "East Region: Generated $1.302M in revenue with a profit margin of 17.8%. "
        "New York City, Philadelphia, and Boston were the top three cities by revenue. "
        "The region benefited from three new corporate account wins totaling $180,000 "
        "in annualized revenue. Customer acquisition cost was $342 per account."
    )
    pdf.add_body_text(
        "West Region: Generated $1.176M with a profit margin of 15.2%. California "
        "accounted for 62% of West region revenue, with San Francisco and Los Angeles "
        "as primary markets. The region experienced supply chain delays averaging 1.3 "
        "days above target due to warehouse capacity constraints in Sacramento."
    )
    pdf.add_body_text(
        "Central Region: Generated $924K with a profit margin of 14.1%. Chicago and "
        "Houston were the dominant markets. The region showed the highest growth rate "
        "at 14.8% YoY, primarily driven by expansion into the Michigan and Minnesota "
        "markets. Average order value was $312, the lowest across regions."
    )
    pdf.add_body_text(
        "South Region: Generated $798K with a profit margin of 12.3%. The region's "
        "lower margin reflects higher shipping costs and a higher proportion of "
        "discounted orders (average discount 16.7% vs. company average 15.3%). "
        "Miami and Atlanta accounted for 71% of regional revenue. We are piloting "
        "a regional distribution center in Charlotte to reduce fulfillment times "
        "from 4.2 days to a target of 2.5 days."
    )

    # Recommendations
    pdf.add_section_title("5. Strategic Recommendations")
    pdf.add_body_text(
        "1. DISCOUNT POLICY: Implement a tiered discount cap structure - maximum 15% "
        "for Technology, 20% for Office Supplies, and 12% for Furniture. This is "
        "projected to improve overall profit margins by 1.8 percentage points."
    )
    pdf.add_body_text(
        "2. INVENTORY OPTIMIZATION: Reduce bookcase inventory by 15% and increase "
        "ergonomic chair inventory by 25% to align with demand trends. Estimated "
        "working capital improvement of $120,000."
    )
    pdf.add_body_text(
        "3. REGIONAL EXPANSION: Accelerate Central region growth by adding 2 sales "
        "representatives in Detroit and Minneapolis. Target: $200K additional revenue "
        "in Q2-Q3 2024."
    )
    pdf.add_body_text(
        "4. SUBSCRIPTION SERVICES: Scale the auto-replenishment program to all Office "
        "Supply customers. Target: $500K in annualized recurring revenue by Q4 2024."
    )
    pdf.add_body_text(
        "5. CUSTOMER RETENTION: Launch a loyalty program for Consumer segment to "
        "improve retention from 78% to target 85%. Estimated customer lifetime value "
        "increase of $230 per account."
    )

    filepath = outdir / "Q1_2024_Market_Analysis_Report.pdf"
    pdf.output(str(filepath))
    return filepath


# ---------------------------------------------------------------------------
# Document 2: Product Return Policy
# ---------------------------------------------------------------------------

def _create_return_policy(outdir: Path) -> Path:
    """Generate Product Return Policy Document PDF."""
    pdf = BusinessPDF("Product Return Policy - Effective January 2024")
    pdf.alias_nb_pages()

    pdf.add_cover_page(
        title="Product Return Policy",
        subtitle="Official Return & Exchange Guidelines",
        date="January 1, 2024",
        author="Operations & Customer Service Department",
    )

    # Overview
    pdf.add_page()
    pdf.add_section_title("1. Return Policy Overview")
    pdf.add_body_text(
        "This document outlines the official return and exchange policies for all "
        "products sold through our retail and B2B channels. These policies are "
        "effective as of January 1, 2024, and supersede all previous return policy "
        "documents. All customer-facing staff and account managers must be familiar "
        "with these guidelines."
    )
    pdf.add_body_text(
        "Our return policy is designed to balance customer satisfaction with "
        "operational efficiency. We aim to process all return requests within "
        "2 business days of receipt and issue refunds within 5 business days "
        "of product inspection. The overall target return rate is below 8% "
        "across all categories."
    )

    # General Policy
    pdf.add_section_title("2. General Return Conditions")
    pdf.add_body_text(
        "Standard Return Window: All products may be returned within 30 days of "
        "the delivery date. The return window is extended to 45 days during the "
        "holiday season (November 15 - January 15). Products must be in their "
        "original packaging with all accessories, manuals, and documentation "
        "included. Items that are damaged due to customer misuse, unauthorized "
        "modification, or normal wear and tear are not eligible for return."
    )
    pdf.add_body_text(
        "Proof of purchase is required for all returns. Acceptable proof includes "
        "the original invoice, order confirmation email, or order number from our "
        "system. Corporate accounts with net-30 or net-60 payment terms may initiate "
        "returns through their dedicated account manager or through the self-service "
        "portal at returns.superstore.com."
    )
    pdf.add_body_text(
        "Restocking fees apply to certain product categories as detailed below. "
        "Restocking fees are waived for defective products, wrong items shipped, "
        "or orders that arrived damaged during transit. All restocking fees are "
        "calculated based on the original purchase price before any discounts."
    )

    # Category Policies
    pdf.add_section_title("3. Category-Specific Return Policies")
    pdf.add_subsection_title("3.1 Technology Products")
    pdf.add_body_text(
        "Laptops and Phones: 30-day return window with a 15% restocking fee for "
        "opened items. Unopened items in original sealed packaging receive a full "
        "refund with no restocking fee. All personal data must be wiped before "
        "return - a factory reset certification form must be completed and included. "
        "Battery degradation below 80% capacity is not covered under the return "
        "policy but may be eligible for warranty service."
    )
    pdf.add_body_text(
        "Accessories and Monitors: 30-day return window with a 10% restocking fee "
        "for opened items. Monitors must be returned in original packaging to prevent "
        "transit damage. Cables, adapters, and small accessories under $25 are "
        "eligible for no-questions-asked returns. Defective monitors are replaced "
        "with an equivalent or upgraded model within 3 business days."
    )

    pdf.add_subsection_title("3.2 Furniture Products")
    pdf.add_body_text(
        "Chairs: 30-day return window with free return shipping for defective items. "
        "Non-defective returns incur a 20% restocking fee AND return shipping charges. "
        "Assembled chairs must be disassembled to original packaging dimensions for "
        "return. The Herman Miller Aeron and Steelcase Leap V2 are eligible for an "
        "extended 60-day trial period - if the customer is not satisfied with comfort "
        "after 60 days, a full refund is issued with no restocking fee."
    )
    pdf.add_body_text(
        "Tables and Desks: Due to the large size and weight of these items, returns "
        "must be coordinated with our logistics team. A pickup will be scheduled "
        "within 5 business days of return approval. A 25% restocking fee applies "
        "for non-defective returns. Standing desks with electronic components "
        "(motors, controllers) have a separate 2-year warranty for mechanical parts."
    )
    pdf.add_body_text(
        "Bookcases: Standard 30-day return policy with 15% restocking fee. Items "
        "that have been wall-mounted are not eligible for return unless defective. "
        "Custom-sized bookcases are final sale and cannot be returned."
    )

    pdf.add_subsection_title("3.3 Office Supplies")
    pdf.add_body_text(
        "Paper Products: Returns accepted only for defective or wrong items. Opened "
        "paper packages cannot be returned due to hygiene and quality concerns. "
        "Bulk orders (10+ cases) may be returned within 14 days if unopened, subject "
        "to a 5% restocking fee. Specialty papers (cotton, linen, recycled premium) "
        "have the same return policy as standard papers."
    )
    pdf.add_body_text(
        "Binders, Storage, and Art Supplies: 30-day return window with no restocking "
        "fee for unopened items. Opened items may be returned within 14 days with a "
        "10% restocking fee. Customized or personalized items (printed binders, "
        "branded storage boxes) are final sale."
    )

    # Refund Process
    pdf.add_section_title("4. Refund Processing")
    pdf.add_body_text(
        "Refunds are processed based on the original payment method. Credit card "
        "refunds typically appear within 5-7 business days after return approval. "
        "Corporate account credits are applied within 2 business days. Check "
        "refunds are mailed within 10 business days."
    )
    pdf.add_body_text(
        "Exchange requests are processed with priority shipping at no additional "
        "cost. If the replacement item has a higher price, the customer will be "
        "charged the difference. If the replacement is lower-priced, a refund for "
        "the difference will be issued. Exchanges do not incur restocking fees."
    )
    pdf.add_body_text(
        "For orders placed with promotional discounts greater than 25%, returns will "
        "be refunded at the discounted price paid, not the original list price. "
        "Gift card purchases are refunded as store credit only. International "
        "orders are subject to the same return policy but customer bears return "
        "shipping costs and any applicable customs duties."
    )

    # Defective Products
    pdf.add_section_title("5. Defective Product Handling")
    pdf.add_body_text(
        "Products that are defective or damaged on arrival (DOA) receive expedited "
        "processing. Customers should report defective items within 48 hours of "
        "delivery for fastest resolution. DOA claims require photographic evidence "
        "submitted through the returns portal or sent to returns@superstore.com."
    )
    pdf.add_body_text(
        "For defective Technology products, we offer three resolution options: "
        "(1) full refund, (2) replacement with same model, or (3) replacement with "
        "equivalent model plus a 10% courtesy discount on next purchase. Our quality "
        "assurance team inspects all returned defective items and data is used to "
        "negotiate warranty claims with manufacturers."
    )
    pdf.add_body_text(
        "Furniture items with manufacturing defects discovered within 90 days of "
        "purchase are covered under our extended defect warranty. This includes "
        "issues like uneven legs, faulty gas cylinders in chairs, and peeling "
        "laminate on desks. Normal wear and tear, scratches from use, and fabric "
        "fading are not considered defects."
    )

    # Return Shipping
    pdf.add_section_title("6. Return Shipping Guidelines")
    pdf.add_body_text(
        "Prepaid return shipping labels are provided for defective items, wrong "
        "items, and orders damaged in transit. For all other returns, customers "
        "may use our discounted return shipping service ($7.99 flat rate for items "
        "under 50 lbs, $14.99 for items 50-100 lbs) or arrange their own shipping."
    )
    pdf.add_body_text(
        "Furniture items over 100 lbs require white-glove pickup service. This "
        "service is complimentary for defective items and costs $49.99 for "
        "non-defective returns. Pickup is available Monday through Saturday, "
        "8 AM to 6 PM local time. Customers must be present or designate an "
        "authorized representative during pickup."
    )

    filepath = outdir / "Product_Return_Policy.pdf"
    pdf.output(str(filepath))
    return filepath


# ---------------------------------------------------------------------------
# Document 3: Sales Strategy Memo
# ---------------------------------------------------------------------------

def _create_sales_strategy(outdir: Path) -> Path:
    """Generate Sales Strategy Memo for 2024 PDF."""
    pdf = BusinessPDF("Sales Strategy Memo - FY2024")
    pdf.alias_nb_pages()

    pdf.add_cover_page(
        title="Sales Strategy Memo",
        subtitle="Fiscal Year 2024 Growth Plan & Targets",
        date="January 10, 2024",
        author="VP of Sales & Business Development",
    )

    # Strategic Vision
    pdf.add_page()
    pdf.add_section_title("1. Strategic Vision for 2024")
    pdf.add_body_text(
        "Our 2024 sales strategy focuses on three pillars: (1) deepening penetration "
        "in existing Corporate accounts, (2) expanding geographic reach in underserved "
        "markets, and (3) launching new revenue streams through subscription-based "
        "services. Our overall revenue target for FY2024 is $18.5 million, representing "
        "a 15% increase over FY2023 actual revenue of $16.1 million."
    )
    pdf.add_body_text(
        "The competitive landscape is intensifying with Amazon Business growing its "
        "B2B market share to 12%. To defend and grow our position, we must differentiate "
        "through superior service, faster delivery, and deeper customer relationships. "
        "Our Net Promoter Score target for 2024 is 62, up from 55 in 2023."
    )

    # Revenue Targets
    pdf.add_section_title("2. Revenue Targets by Category")
    pdf.add_subsection_title("2.1 Technology - Target: $8.14M (+19%)")
    pdf.add_body_text(
        "Technology will be our primary growth driver in 2024. Key initiatives include: "
        "(a) launching a Device-as-a-Service (DaaS) program for Corporate accounts, "
        "offering laptop and phone leasing with refresh cycles every 24 months, "
        "(b) expanding our monitor lineup to include ultrawide and curved options, "
        "and (c) introducing managed IT accessories bundles priced at $299/employee."
    )
    pdf.add_body_text(
        "The DaaS program alone is projected to generate $1.2M in new annual recurring "
        "revenue by Q4 2024. Initial pilot with 5 Corporate accounts in Q1 showed "
        "strong interest, with 3 accounts committing to 100+ device contracts. "
        "Average DaaS contract value is $48 per device per month, with 36-month "
        "minimum commitments."
    )

    pdf.add_subsection_title("2.2 Furniture - Target: $5.37M (+12%)")
    pdf.add_body_text(
        "Furniture growth will be driven by the continuing hybrid work trend and "
        "corporate office renovation cycles. We will focus on solution selling - "
        "offering complete workstation packages (desk + chair + monitor arm + "
        "accessories) at bundled pricing with 8-12% savings versus individual "
        "purchase. Target: 200 workstation bundle sales in 2024."
    )
    pdf.add_body_text(
        "We are partnering with two new furniture manufacturers to introduce a "
        "mid-price ergonomic chair line ($400-600 range) to compete with IKEA "
        "and Autonomous. This fills a gap between our economy ($200-350) and "
        "premium ($1,000+) offerings. Launch is planned for Q2 2024 with an "
        "initial inventory of 500 units across 4 SKUs."
    )

    pdf.add_subsection_title("2.3 Office Supplies - Target: $4.99M (+10%)")
    pdf.add_body_text(
        "Office Supplies growth will be driven primarily by the auto-replenishment "
        "subscription service and expansion into new product categories. The "
        "subscription service target is 1,200 active subscribers by December 2024, "
        "each generating an average of $35 per month in recurring orders."
    )
    pdf.add_body_text(
        "New product category additions for 2024 include: breakroom supplies "
        "(coffee, snacks, cleaning products), shipping and packaging materials, "
        "and safety/wellness products (first aid kits, sanitizers, ergonomic "
        "accessories). These new categories are projected to add $420,000 in "
        "revenue for the year."
    )

    # Regional Strategy
    pdf.add_section_title("3. Regional Sales Strategy")
    pdf.add_subsection_title("3.1 East Region - Target: $5.74M")
    pdf.add_body_text(
        "The East region will maintain its position as our largest revenue generator. "
        "Key focus areas: (a) deepen relationships with 15 top Corporate accounts in "
        "NYC and Boston, targeting 20% wallet share increase, (b) launch dedicated "
        "government sales team for state and local government accounts in Pennsylvania "
        "and Connecticut, targeting $400K in new government revenue."
    )
    pdf.add_body_text(
        "We are hiring 3 additional Business Development Representatives for the East "
        "region, bringing the total team to 12. Each BDR is expected to generate "
        "$180K in new business pipeline per quarter. Total East region sales headcount "
        "including Account Executives and Sales Engineers will be 28."
    )

    pdf.add_subsection_title("3.2 West Region - Target: $5.18M")
    pdf.add_body_text(
        "West region strategy centers on the tech corridor from San Francisco to "
        "Seattle. We will target startups and scale-ups (50-200 employees) with "
        "our new Startup Office Package - a complete office setup bundle with "
        "flexible payment terms. Target: 50 new startup accounts in 2024."
    )
    pdf.add_body_text(
        "The Sacramento distribution center expansion (adding 15,000 sq ft) will "
        "be completed by March 2024, enabling same-day delivery in the SF Bay Area "
        "and next-day delivery across California. This is expected to reduce cart "
        "abandonment by 8% and increase average order frequency from 3.2 to 4.1 "
        "orders per quarter per account."
    )

    pdf.add_subsection_title("3.3 Central Region - Target: $4.07M")
    pdf.add_body_text(
        "Central region will focus on aggressive expansion in Detroit, Minneapolis, "
        "and Columbus. We are opening a regional office in Detroit in Q2 2024 with "
        "a 5-person sales team. The Central region has the lowest customer penetration "
        "rate (2.3% vs. company average of 4.1%), presenting significant growth "
        "opportunity."
    )
    pdf.add_body_text(
        "Partnership with three regional office furniture dealers will extend our "
        "reach into the mid-market. These partners will receive 12% commission on "
        "referred sales and access to our full product catalog via API integration. "
        "Target partner-sourced revenue: $300K in 2024."
    )

    pdf.add_subsection_title("3.4 South Region - Target: $3.51M")
    pdf.add_body_text(
        "South region growth will be supported by the new Charlotte distribution "
        "center (operational Q2 2024) and expansion into Nashville and Knoxville "
        "markets. We are investing $180,000 in regional marketing campaigns "
        "focused on LinkedIn and industry trade shows."
    )
    pdf.add_body_text(
        "The South region's higher shipping costs (18% above national average) "
        "have been a persistent challenge. The Charlotte DC is expected to reduce "
        "average shipping cost per order from $12.40 to $8.20, improving regional "
        "profit margins by approximately 3.4 percentage points."
    )

    # Sales Team Structure
    pdf.add_section_title("4. Sales Team & Compensation")
    pdf.add_body_text(
        "Total sales team for 2024: 85 members (up from 72 in 2023). Breakdown: "
        "32 Account Executives, 24 Business Development Representatives, 12 Sales "
        "Engineers, 8 Account Managers (Corporate), 5 Regional Sales Directors, "
        "and 4 Sales Operations Analysts."
    )
    pdf.add_body_text(
        "Compensation structure for 2024: Base salary represents 60% of OTE "
        "(On-Target Earnings) with 40% variable commission. Accelerators kick in "
        "at 110% quota attainment with uncapped earnings potential. Average OTE "
        "for Account Executives: $125,000. Average OTE for BDRs: $72,000. "
        "Quarterly President's Club trips for top 10% performers."
    )
    pdf.add_body_text(
        "New for 2024: Customer Success Bonus - Account Executives earn an additional "
        "5% commission on renewed and expanded accounts. This incentivizes retention "
        "alongside new business acquisition. Customer churn target: below 9% for "
        "Corporate accounts and below 22% for Consumer accounts."
    )

    # Key Initiatives
    pdf.add_section_title("5. Key Growth Initiatives")
    pdf.add_body_text(
        "Initiative 1 - AI-Powered Sales Enablement: Deploy an AI sales assistant "
        "that analyzes customer purchase history, predicts reorder timing, and "
        "recommends cross-sell opportunities. Budget: $150,000. Expected ROI: "
        "7% increase in average order value within 6 months of deployment."
    )
    pdf.add_body_text(
        "Initiative 2 - Customer Portal 2.0: Launch redesigned self-service portal "
        "with features including real-time inventory visibility, automated quote "
        "generation, order tracking, and spend analytics dashboard. Budget: $280,000. "
        "Target: 40% of orders placed through portal by Q4 (currently 18%)."
    )
    pdf.add_body_text(
        "Initiative 3 - Sustainability Program: Launch eco-friendly product line "
        "and carbon-neutral shipping option. 67% of Corporate procurement managers "
        "indicated sustainability is a factor in vendor selection (up from 41% in "
        "2022). Premium pricing of 5-8% on eco-certified products is acceptable "
        "to 78% of surveyed Corporate customers."
    )
    pdf.add_body_text(
        "Initiative 4 - Same-Day Delivery Expansion: Extend same-day delivery "
        "from current 5 metros to 12 metros by Q3 2024. Investment: $420,000 in "
        "last-mile logistics partnerships. Same-day delivery customers have 2.3x "
        "higher retention rates and 34% higher average order values."
    )

    # Metrics and KPIs
    pdf.add_section_title("6. Key Performance Indicators for 2024")
    pdf.add_body_text(
        "Revenue KPIs: Total revenue $18.5M, new customer revenue $3.2M, recurring "
        "revenue $2.1M, average deal size $485 (up from $442). Profitability KPIs: "
        "Gross margin 21.5% (up from 19.8%), operating margin 12.3%, average "
        "discount rate below 14% (down from 15.3%)."
    )
    pdf.add_body_text(
        "Sales Efficiency KPIs: Sales cycle length 18 days (down from 22 days), "
        "quote-to-close ratio 38% (up from 32%), pipeline coverage ratio 3.5x, "
        "cost of customer acquisition below $280. Customer KPIs: NPS 62, "
        "customer retention rate 88%, customer lifetime value $4,200, repeat "
        "purchase rate 72%."
    )

    filepath = outdir / "Sales_Strategy_Memo_2024.pdf"
    pdf.output(str(filepath))
    return filepath


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_all_docs(outdir: str | Path = "data/docs") -> list[Path]:
    """Generate all 3 sample business documents.

    Args:
        outdir: Directory to write PDFs into.

    Returns:
        List of Paths to the generated PDF files.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("Generating sample business documents ...")
    files: list[Path] = []

    f1 = _create_market_analysis(outdir)
    print(f"  [OK] {f1.name}")
    files.append(f1)

    f2 = _create_return_policy(outdir)
    print(f"  [OK] {f2.name}")
    files.append(f2)

    f3 = _create_sales_strategy(outdir)
    print(f"  [OK] {f3.name}")
    files.append(f3)

    print(f"Done - {len(files)} documents generated in {outdir}/")
    return files


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate sample business PDFs")
    parser.add_argument("--outdir", default="data/docs", help="Output directory")
    args = parser.parse_args()
    generate_all_docs(outdir=args.outdir)
