import os
import logging
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
except OSError:
    # Handles GTK missing on Windows
    WEASYPRINT_AVAILABLE = False

logger = logging.getLogger(__name__)

class ScribeService:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), "../templates/contracts")
        self.output_dir = os.path.join(os.path.dirname(__file__), "../../generated_contracts")
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def generate_contract_pdf(self, offer_data: dict) -> str:
        """
        Generates a PDF contract from offer data.
        Returns the absolute path to the generated file.
        """
        try:
            template = self.env.get_template("psa.html")
            
            # Prepare context with defaults
            context = {
                "date": datetime.now().strftime("%B %d, %Y"),
                "seller_name": offer_data.get("seller_name", "__________________"),
                "buyer_name": offer_data.get("buyer_name", "ARELA Holdings LLC"),
                "property_address": offer_data.get("property_address", "Unknown Address"),
                "purchase_price": f"{offer_data.get('offer_amount', 0):,}",
                "earnest_money": f"{offer_data.get('earnest_money', 1000):,}",
                "closing_date": offer_data.get("closing_date", "30 Days from Acceptance"),
                "inspection_period": offer_data.get("inspection_period", 10)
            }
            
            html_content = template.render(context)
            
            filename = f"PSA_{offer_data.get('lead_id', 'draft')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            if WEASYPRINT_AVAILABLE:
                pdf_path = os.path.join(self.output_dir, f"{filename}.pdf")
                HTML(string=html_content).write_pdf(pdf_path)
                logger.info(f"Contract generated: {pdf_path}")
                return pdf_path
            else:
                # Fallback to HTML if WeasyPrint fails (e.g. missing GTK)
                html_path = os.path.join(self.output_dir, f"{filename}.html")
                with open(html_path, "w") as f:
                    f.write(html_content)
                logger.warning(f"WeasyPrint unavailable. Generated HTML instead: {html_path}")
                return html_path

        except Exception as e:
            logger.error(f"Failed to generate contract: {str(e)}")
            raise RuntimeError(f"Contract generation failed: {str(e)}")
