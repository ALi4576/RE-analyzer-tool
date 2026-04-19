"""
Export module for converting requirements to Jira/Trello tickets.
Handles ticket creation and updates via API integration.
"""
from typing import List, Dict, Optional, Any
import uuid
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
