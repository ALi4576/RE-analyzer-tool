"""
Export module for converting requirements to Jira/Trello tickets and PDF.
"""
from typing import List, Dict, Optional, Any
import uuid
import os
import tempfile
from datetime import datetime
from config import settings
from models.schemas import (
    ISORequirement,
    FormalizedRequirement,
    ExportResult,
)
from utils import get_logger

logger = get_logger("export")


class JiraExporter:
    """Export ISO requirements to Jira tickets."""
    
    def __init__(self):
        """Initialize Jira exporter."""
        if not settings.JIRA_ENABLED:
            logger.warning("Jira exporter initialized but JIRA_ENABLED=False")
            self.client = None
            return
        
        try:
            from jira import JIRA
            
            self.client = JIRA(
                server=settings.JIRA_SERVER_URL,
                basic_auth=(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN),
            )
            logger.info("Jira client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Jira client: {str(e)}")
            self.client = None
    
    def export_requirements(
        self, iso_requirements: List[ISORequirement], project_key: Optional[str] = None
    ) -> ExportResult:
        """
        Export requirements as Jira tickets.
        
        Args:
            iso_requirements: List of ISO requirements to export
            project_key: Jira project key (uses default if not provided)
            
        Returns:
            ExportResult with ticket IDs and status
        """
        if not self.client:
            logger.error("Jira client not initialized")
            return ExportResult(
                export_id=str(uuid.uuid4()),
                target="jira",
                ticket_ids=[],
                status="failed",
                url=None,
            )
        
        project_key = project_key or settings.JIRA_PROJECT_KEY
        ticket_ids = []
        
        try:
            logger.info(f"Exporting {len(iso_requirements)} requirements to Jira project {project_key}")
            
            for requirement in iso_requirements:
                issue_dict = {
                    "project": {"key": project_key},
                    "summary": requirement.title,
                    "description": self._format_jira_description(requirement),
                    "issuetype": {"name": "Story"},
                    "priority": {"name": self._map_priority(requirement.priority)},
                    "customfield_10000": requirement.requirement_id,  # Custom field for requirement ID
                }
                
                issue = self.client.create_issue(fields=issue_dict)
                ticket_ids.append(issue.key)
                logger.info(f"Created Jira ticket {issue.key} for {requirement.requirement_id}")
            
            project_url = f"{settings.JIRA_SERVER_URL}/browse/{project_key}"
            
            return ExportResult(
                export_id=str(uuid.uuid4()),
                target="jira",
                ticket_ids=ticket_ids,
                status="success",
                url=project_url,
            )
            
        except Exception as e:
            logger.error(f"Jira export error: {str(e)}")
            return ExportResult(
                export_id=str(uuid.uuid4()),
                target="jira",
                ticket_ids=ticket_ids,
                status="failed",
                url=None,
            )
    
    def _format_jira_description(self, requirement: ISORequirement) -> str:
        """Format requirement as Jira ticket description."""
        description = f"""
{requirement.shall_statement}

h3. Rationale
{requirement.rationale}

h3. Acceptance Criteria
* {chr(10).join('* ' + criterion for criterion in requirement.acceptance_criteria)}

h3. Category
{requirement.category}

h3. Requirement ID
{requirement.requirement_id}
"""
        return description.strip()
    
    def _map_priority(self, iso_priority: str) -> str:
        """Map ISO priority to Jira priority."""
        priority_map = {
            "High": "Highest",
            "Medium": "Medium",
            "Low": "Lowest",
        }
        return priority_map.get(iso_priority, "Medium")


class TrelloExporter:
    """Export ISO requirements to Trello cards."""
    
    def __init__(self):
        """Initialize Trello exporter."""
        if not settings.TRELLO_ENABLED:
            logger.warning("Trello exporter initialized but TRELLO_ENABLED=False")
            self.client = None
            return
        
        try:
            from trello import TrelloClient
            
            self.client = TrelloClient(
                api_key=settings.TRELLO_API_KEY,
                api_secret=settings.TRELLO_API_TOKEN,
            )
            logger.info("Trello client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Trello client: {str(e)}")
            self.client = None
    
    def export_requirements(
        self, iso_requirements: List[ISORequirement], board_id: Optional[str] = None
    ) -> ExportResult:
        """
        Export requirements as Trello cards.
        
        Args:
            iso_requirements: List of ISO requirements to export
            board_id: Trello board ID (uses default if not provided)
            
        Returns:
            ExportResult with card IDs and status
        """
        if not self.client:
            logger.error("Trello client not initialized")
            return ExportResult(
                export_id=str(uuid.uuid4()),
                target="trello",
                ticket_ids=[],
                status="failed",
                url=None,
            )
        
        board_id = board_id or settings.TRELLO_BOARD_ID
        card_ids = []
        
        try:
            logger.info(f"Exporting {len(iso_requirements)} requirements to Trello board {board_id}")
            
            board = self.client.get_board(board_id)
            list_name = "Requirements"
            
            # Find or create list
            req_list = None
            for list_obj in board.list_lists("all"):
                if list_obj.name == list_name:
                    req_list = list_obj
                    break
            
            if not req_list:
                req_list = board.add_list(list_name)
            
            for requirement in iso_requirements:
                card = req_list.add_card(
                    name=requirement.title,
                    desc=self._format_trello_description(requirement),
                )
                card_ids.append(card.id)
                logger.info(f"Created Trello card {card.id} for {requirement.requirement_id}")
            
            board_url = f"https://trello.com/b/{board_id}"
            
            return ExportResult(
                export_id=str(uuid.uuid4()),
                target="trello",
                ticket_ids=card_ids,
                status="success",
                url=board_url,
            )
            
        except Exception as e:
            logger.error(f"Trello export error: {str(e)}")
            return ExportResult(
                export_id=str(uuid.uuid4()),
                target="trello",
                ticket_ids=card_ids,
                status="failed",
                url=None,
            )
    
    def _format_trello_description(self, requirement: ISORequirement) -> str:
        """Format requirement as Trello card description."""
        description = f"""
{requirement.shall_statement}

**Rationale:**
{requirement.rationale}

**Acceptance Criteria:**
{chr(10).join([f"- {criterion}" for criterion in requirement.acceptance_criteria])}

**Category:** {requirement.category}
**Priority:** {requirement.priority}
**Requirement ID:** {requirement.requirement_id}
"""
        return description.strip()


class PdfExporter:
    """Generate a formatted ISO 29148 requirements PDF."""

    def export_requirements(
        self, iso_requirements: List[ISORequirement], session_id: str = ""
    ) -> str:
        """
        Generate a PDF from requirements and return the file path.

        Args:
            iso_requirements: List of ISO requirements
            session_id: Used for the output filename

        Returns:
            Absolute path to the generated PDF file
        """
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak,
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER

        out_dir = os.path.join(settings.UPLOAD_DIR, session_id or "pdf_export")
        os.makedirs(out_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.join(out_dir, f"requirements_{timestamp}.pdf")

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title", parent=styles["Heading1"],
            fontSize=20, spaceAfter=6, textColor=colors.HexColor("#1e3a5f"),
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle", parent=styles["Normal"],
            fontSize=10, textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER, spaceAfter=20,
        )
        req_title_style = ParagraphStyle(
            "ReqTitle", parent=styles["Heading2"],
            fontSize=13, textColor=colors.HexColor("#1e3a5f"),
            spaceBefore=14, spaceAfter=4,
        )
        label_style = ParagraphStyle(
            "Label", parent=styles["Normal"],
            fontSize=9, textColor=colors.HexColor("#777777"),
            fontName="Helvetica-Bold", spaceBefore=6,
        )
        body_style = ParagraphStyle(
            "Body", parent=styles["Normal"],
            fontSize=10, leading=14, spaceAfter=2,
        )
        badge_style = ParagraphStyle(
            "Badge", parent=styles["Normal"],
            fontSize=9, textColor=colors.white,
            fontName="Helvetica-Bold",
        )

        story = []

        # ── Cover ──────────────────────────────────────────────────────────
        story.append(Spacer(1, 2 * cm))
        story.append(Paragraph("Software Requirements Specification", title_style))
        story.append(Paragraph(
            f"ISO 29148 Compliant · Generated {datetime.now().strftime('%B %d, %Y %H:%M')}",
            subtitle_style,
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3a5f")))
        story.append(Spacer(1, 0.4 * cm))

        # Summary table
        summary_data = [
            ["Total Requirements", str(len(iso_requirements))],
            ["Standard", "ISO/IEC/IEEE 29148:2018"],
            ["Session ID", session_id or "—"],
        ]
        summary_table = Table(summary_data, colWidths=[5 * cm, 10 * cm])
        summary_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1e3a5f")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(summary_table)
        story.append(PageBreak())

        # ── Requirements ───────────────────────────────────────────────────
        priority_colors = {
            "High": colors.HexColor("#c0392b"),
            "Medium": colors.HexColor("#e67e22"),
            "Low": colors.HexColor("#27ae60"),
        }

        for req in iso_requirements:
            req_id = getattr(req, "requirement_id", None) or (req.get("requirement_id") if isinstance(req, dict) else "REQ-????")
            title = getattr(req, "title", None) or (req.get("title") if isinstance(req, dict) else "Untitled")
            shall = getattr(req, "shall_statement", None) or (req.get("shall_statement") if isinstance(req, dict) else "")
            rationale = getattr(req, "rationale", None) or (req.get("rationale") if isinstance(req, dict) else "")
            criteria = getattr(req, "acceptance_criteria", None) or (req.get("acceptance_criteria") if isinstance(req, dict) else [])
            priority = getattr(req, "priority", None) or (req.get("priority") if isinstance(req, dict) else "Medium")
            category = getattr(req, "category", None) or (req.get("category") if isinstance(req, dict) else "Functional")

            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))
            story.append(Paragraph(f"{req_id} — {title}", req_title_style))

            # Priority badge via coloured table cell
            p_color = priority_colors.get(str(priority), colors.HexColor("#888888"))
            badge_table = Table([[priority or "Medium"]], colWidths=[2.2 * cm])
            badge_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), p_color),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROUNDEDCORNERS", [3, 3, 3, 3]),
            ]))
            story.append(badge_table)
            story.append(Spacer(1, 0.2 * cm))

            story.append(Paragraph("SHALL STATEMENT", label_style))
            story.append(Paragraph(str(shall), body_style))

            if rationale:
                story.append(Paragraph("RATIONALE", label_style))
                story.append(Paragraph(str(rationale), body_style))

            if criteria:
                story.append(Paragraph("ACCEPTANCE CRITERIA", label_style))
                for criterion in (criteria if isinstance(criteria, list) else [criteria]):
                    story.append(Paragraph(f"• {criterion}", body_style))

            story.append(Paragraph("CATEGORY", label_style))
            story.append(Paragraph(str(category), body_style))
            story.append(Spacer(1, 0.3 * cm))

        doc.build(story)
        logger.info(f"PDF export written to {pdf_path}")
        return pdf_path


class ExportManager:
    """Manages export operations for both Jira and Trello."""
    
    def __init__(self):
        """Initialize export manager with all backends."""
        self.jira_exporter = JiraExporter()
        self.trello_exporter = TrelloExporter()
        logger.info("Export Manager initialized")
    
    def export(
        self, formalized_req: FormalizedRequirement, target: str = "jira"
    ) -> ExportResult:
        """
        Export formatted requirements to specified target.
        
        Args:
            formalized_req: Formalized requirements object
            target: "jira" or "trello"
            
        Returns:
            ExportResult with status and ticket IDs
        """
        logger.info(f"Starting export to {target}")
        
        if target.lower() == "jira":
            return self.jira_exporter.export_requirements(formalized_req.iso_requirements)
        elif target.lower() == "trello":
            return self.trello_exporter.export_requirements(formalized_req.iso_requirements)
        else:
            logger.error(f"Unknown export target: {target}")
            return ExportResult(
                export_id=str(uuid.uuid4()),
                target=target,
                ticket_ids=[],
                status="failed",
                url=None,
            )
    
    def dry_run(
        self, formalized_req: FormalizedRequirement, target: str = "jira"
    ) -> Dict[str, Any]:
        """
        Preview what would be exported without actually creating tickets.
        
        Args:
            formalized_req: Formalized requirements
            target: Export target
            
        Returns:
            Dict with preview of what would be created
        """
        logger.info(f"Performing dry-run export to {target}")
        
        preview = {
            "target": target,
            "total_items": len(formalized_req.iso_requirements),
            "items": [],
        }
        
        if target.lower() == "jira":
            for req in formalized_req.iso_requirements:
                preview["items"].append({
                    "type": "Jira Story",
                    "summary": req.title,
                    "priority": self.jira_exporter._map_priority(req.priority),
                    "description_preview": req.shall_statement[:100],
                })
        
        elif target.lower() == "trello":
            for req in formalized_req.iso_requirements:
                preview["items"].append({
                    "type": "Trello Card",
                    "name": req.title,
                    "description_preview": req.shall_statement[:100],
                })
        
        logger.info(f"Dry-run preview created with {len(preview['items'])} items")
        return preview


# Global export manager instance
_export_manager = None


def get_export_manager() -> ExportManager:
    """Get or initialize the global export manager instance."""
    global _export_manager
    if _export_manager is None:
        _export_manager = ExportManager()
    return _export_manager
