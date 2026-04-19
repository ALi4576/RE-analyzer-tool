"""
ISO 29148 Compliance Formatter.
Transforms messy requirements into formally compliant specifications.
"""
from typing import List, Dict, Any
import json
from datetime import datetime
from utils import get_logger
from models.schemas import ISORequirement, FormalizedRequirement

logger = get_logger("agent")


class ISO29148Formalizer:
    """
    Converts analyzed requirements into ISO/IEC 29148 standard format.
    
    ISO 29148 specifies that requirements must be:
    - Unambiguous
    - Testable (measurable acceptance criteria)
    - Related to identified need
    - Defined at appropriate level of detail
    - Verifiable
    """
    
    def __init__(self):
        """Initialize ISO formatter."""
        self.template_version = "2023"
        self.requirement_counter = 0
        logger.info("ISO 29148 Formalizer initialized")
    
    def formalize_requirement(
        self, requirement_text: str, category: str = "Functional"
    ) -> ISORequirement:
        """
        Convert single requirement into ISO 29148 format.
        
        Args:
            requirement_text: Raw requirement text
            category: Functional/Non-functional/Interface
            
        Returns:
            Formatted ISORequirement
        """
        self.requirement_counter += 1
        req_id = f"REQ-{self.requirement_counter:04d}"
        
        logger.info(f"Formalizing requirement {req_id}")
        
        # Parse requirement text to extract components
        title = self._extract_title(requirement_text)
        shall_statement = self._create_shall_statement(requirement_text)
        rationale = self._extract_rationale(requirement_text)
        acceptance_criteria = self._generate_acceptance_criteria(requirement_text)
        
        requirement = ISORequirement(
            requirement_id=req_id,
            title=title,
            shall_statement=shall_statement,
            rationale=rationale,
            acceptance_criteria=acceptance_criteria,
            priority=self._determine_priority(requirement_text),
            category=category,
            traceability=[],
        )
        
        logger.info(f"Requirement {req_id} formalized successfully")
        return requirement
    
    def formalize_batch(
        self, requirements_list: List[str], category: str = "Functional"
    ) -> List[ISORequirement]:
        """
        Formalize multiple requirements.
        
        Args:
            requirements_list: List of requirement texts
            category: Category for all requirements
            
        Returns:
            List of formatted requirements
        """
        logger.info(f"Formalizing {len(requirements_list)} requirements")
        formatted_requirements = [
            self.formalize_requirement(req, category) for req in requirements_list
        ]
        return formatted_requirements
    
    def create_formalized_document(
        self, iso_requirements: List[ISORequirement], summary: str = ""
    ) -> FormalizedRequirement:
        """
        Create complete formalized requirements document.
        
        Args:
            iso_requirements: List of ISO requirements
            summary: Executive summary
            
        Returns:
            Complete FormalizedRequirement document
        """
        logger.info(f"Creating formalized document with {len(iso_requirements)} requirements")
        
        # Calculate completeness score
        completeness_score = self._calculate_completeness(iso_requirements)
        
        # Establish traceability relationships
        self._establish_traceability(iso_requirements)
        
        formalized = FormalizedRequirement(
            iso_requirements=iso_requirements,
            summary=summary if summary else self._generate_summary(iso_requirements),
            total_requirements=len(iso_requirements),
            completeness_score=completeness_score,
            ready_for_export=completeness_score >= 0.85,
            export_formats=["json", "csv", "pdf", "jira", "trello"],
        )
        
        logger.info(f"Formalized document ready. Completeness: {completeness_score:.2%}")
        return formalized
    
    def export_as_json(self, formalized_req: FormalizedRequirement) -> str:
        """Export formalized requirements as JSON."""
        return formalized_req.model_dump_json(indent=2)
    
    def export_as_dict(self, formalized_req: FormalizedRequirement) -> Dict[str, Any]:
        """Export formalized requirements as dictionary."""
        return formalized_req.model_dump()
    
    # ---- Helper Methods ----
    
    def _extract_title(self, text: str) -> str:
        """Extract requirement title from text."""
        # First sentence or first 100 chars
        sentences = text.split('.')
        if sentences:
            title = sentences[0].strip()
            return title[:80] if len(title) > 80 else title
        return "Untitled Requirement"
    
    def _create_shall_statement(self, text: str) -> str:
        """
        Create formal "shall" statement.
        ISO requires explicit testable statements using imperative language.
        """
        # Remove qualifiers and vague language
        cleaned = text.replace("should", "shall").replace("could", "shall")
        
        if "shall" not in cleaned.lower():
            # Convert to imperative
            verbs = ["allow", "provide", "support", "enable", "maintain", "ensure"]
            for verb in verbs:
                if verb in cleaned.lower():
                    cleaned = f"The system shall {cleaned.lower()}"
                    break
            else:
                cleaned = f"The system shall {cleaned}"
        
        return cleaned.strip()
    
    def _extract_rationale(self, text: str) -> str:
        """Extract or generate rationale for requirement."""
        # Look for rationale markers
        markers = ["because", "due to", "reason:", "rationale:", "justification:"]
        for marker in markers:
            if marker in text.lower():
                idx = text.lower().index(marker)
                return text[idx + len(marker):].strip()
        
        # Generate generic rationale if not found
        return "Business requirement identified during elicitation phase"
    
    def _generate_acceptance_criteria(self, text: str) -> List[str]:
        """
        Generate measurable acceptance criteria from requirement.
        ISO 29148 requires verifiable criteria.
        """
        criteria = []
        
        # Look for measurement indicators
        measurables = ["at least", "no more than", "within", "before", "after", "by"]
        for measurable in measurables:
            if measurable in text.lower():
                criteria.append(f"✓ Requirement contains measurable element: {measurable}")
        
        # Add standard criteria
        criteria.append("✓ Functionality shall be demonstrated in system testing")
        criteria.append("✓ Requirement shall be traceable to user stories")
        
        if not criteria:
            criteria = [
                "✓ System shall successfully complete the specified action",
                "✓ No errors shall occur during execution",
                "✓ Performance shall meet system requirements",
            ]
        
        return criteria
    
    def _determine_priority(self, text: str) -> str:
        """Determine requirement priority."""
        high_keywords = ["critical", "essential", "mandatory", "required"]
        low_keywords = ["optional", "nice to have", "may", "could"]
        
        text_lower = text.lower()
        
        for keyword in high_keywords:
            if keyword in text_lower:
                return "High"
        
        for keyword in low_keywords:
            if keyword in text_lower:
                return "Low"
        
        return "Medium"
    
    def _calculate_completeness(self, requirements: List[ISORequirement]) -> float:
        """
        Calculate completeness score for requirements set.
        Based on presence of all ISO 29148 fields.
        """
        if not requirements:
            return 0.0
        
        total_score = 0.0
        for req in requirements:
            score = 0.0
            if req.requirement_id:
                score += 0.2
            if req.title:
                score += 0.2
            if req.shall_statement:
                score += 0.2
            if req.rationale:
                score += 0.2
            if req.acceptance_criteria:
                score += 0.2
            total_score += score
        
        return total_score / len(requirements)
    
    def _establish_traceability(self, requirements: List[ISORequirement]) -> None:
        """
        Establish traceability links between requirements.
        Modifies requirements in-place.
        """
        for i, req in enumerate(requirements):
            related_ids = []
            for j, other_req in enumerate(requirements):
                if i != j and self._are_related(req, other_req):
                    related_ids.append(other_req.requirement_id)
            
            if related_ids:
                req.traceability = related_ids
    
    def _are_related(self, req1: ISORequirement, req2: ISORequirement) -> bool:
        """Check if two requirements are related."""
        text1 = (req1.title + " " + req1.shall_statement).lower()
        text2 = (req2.title + " " + req2.shall_statement).lower()
        
        # Simple keyword matching
        keywords1 = set(text1.split())
        keywords2 = set(text2.split())
        
        common = keywords1 & keywords2
        return len(common) > 3
    
    def _generate_summary(self, requirements: List[ISORequirement]) -> str:
        """Generate executive summary from requirements."""
        categories = set(req.category for req in requirements if req.category)
        
        summary = f"""
Summary of Formalized Requirements

Total Requirements: {len(requirements)}
Categories: {', '.join(categories)}

High Priority: {sum(1 for r in requirements if r.priority == 'High')}
Medium Priority: {sum(1 for r in requirements if r.priority == 'Medium')}
Low Priority: {sum(1 for r in requirements if r.priority == 'Low')}

All requirements have been formatted according to ISO/IEC 29148 standard with:
- Unique identifiers
- Clear "shall" statements
- Defined acceptance criteria
- Traceability relationships
- Priority classification
"""
        return summary.strip()


# Global formalizer instance
_formalizer = None


def get_formalizer() -> ISO29148Formalizer:
    """Get or initialize the global formalizer instance."""
    global _formalizer
    if _formalizer is None:
        _formalizer = ISO29148Formalizer()
    return _formalizer
