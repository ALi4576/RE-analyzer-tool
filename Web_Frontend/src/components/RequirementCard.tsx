import React from 'react';
import { ISORequirement } from '../types';
import './RequirementCard.css';

interface RequirementCardProps {
  requirement: ISORequirement;
  completeness_score: number;
  is_highlighted?: boolean;
  is_focused?: boolean;
}

export const RequirementCard: React.FC<RequirementCardProps> = ({
  requirement,
  completeness_score,
  is_highlighted = false,
  is_focused = false,
}) => {
  const getStatusBadge = () => {
    if (completeness_score >= 0.8) {
      return { label: 'ISO-VERIFIED', color: 'green', icon: '✓' };
    } else if (completeness_score >= 0.5) {
      return { label: 'DRAFT', color: 'yellow', icon: '✎' };
    } else {
      return { label: 'INCOMPLETE', color: 'red', icon: '!' };
    }
  };

  const status = getStatusBadge();

  return (
    <div
      className={`requirement-card ${is_highlighted ? 'highlighted' : ''} ${
        is_focused ? 'focused' : ''
      }`}
    >
      <div className="card-header">
        <div className="card-id-and-status">
          <span className="requirement-id">{requirement.requirement_id}</span>
          <span className={`status-badge status-${status.color}`}>
            {status.icon} {status.label}
          </span>
        </div>
        <div className="completeness-indicator">
          <div className="completeness-bar">
            <div
              className={`completeness-fill status-${status.color}`}
              style={{ width: `${completeness_score * 100}%` }}
            ></div>
          </div>
          <span className="completeness-text">{Math.round(completeness_score * 100)}%</span>
        </div>
      </div>

      <div className="card-title">{requirement.title}</div>

      <div className="card-shall-section">
        <div className="card-label">SHALL STATEMENT</div>
        <div className="card-shall">"{requirement.shall_statement}"</div>
      </div>

      <div className="card-rationale-section">
        <div className="card-label">RATIONALE</div>
        <div className="card-rationale">{requirement.rationale}</div>
      </div>

      {requirement.acceptance_criteria && requirement.acceptance_criteria.length > 0 && (
        <div className="card-acceptance-section">
          <div className="card-label">ACCEPTANCE CRITERIA</div>
          <ul className="card-acceptance-list">
            {requirement.acceptance_criteria.map((criterion, idx) => (
              <li key={idx}>{criterion}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="card-footer">
        <div className="card-meta">
          <span className={`priority priority-${requirement.priority?.toLowerCase() || 'medium'}`}>
            {requirement.priority?.toUpperCase() || 'MEDIUM'}
          </span>
          <span className="category">{requirement.category?.replace(/_/g, ' ') || 'FUNCTIONAL'}</span>
        </div>
      </div>
    </div>
  );
};

export default RequirementCard;
