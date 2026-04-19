import React, { useState } from 'react';
import { HelpCircle, Send } from 'lucide-react';
import { ClarificationQuestion } from '@/types/index';
import { LoadingSpinner } from './Loading';

interface ClarificationPanelProps {
  questions: ClarificationQuestion[] | null;
  onSubmit: (clarifications: Record<string, string>) => Promise<void>;
  isLoading: boolean;
}

export const ClarificationPanel: React.FC<ClarificationPanelProps> = ({
  questions,
  onSubmit,
  isLoading,
}) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});

  if (!questions || questions.length === 0) {
    return null;
  }

  const handleAnswerChange = (questionId: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (Object.keys(answers).length === questions.length) {
      try {
        const response = await fetch('/api/clarify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ clarifications: answers }),
        });

        if (!response.ok) {
          throw new Error('Failed to submit clarifications');
        }

        await onSubmit(answers);
        setAnswers({});
      } catch (error) {
        console.error('Clarification submission error:', error);
        alert('Failed to submit clarifications');
      }
    }
  };

  const allQuestionsAnswered = questions.every((q) => answers[q.question_id]);

  if (isLoading) {
    return <LoadingSpinner message="Processing clarifications..." />;
  }

  return (
    <div className="animate-slide-in">
      <div className="card p-6 border-2 border-yellow-200 bg-yellow-50">
        <div className="flex items-start gap-3 mb-4">
          <HelpCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-yellow-900">Clarification Questions</h3>
            <p className="text-sm text-yellow-700 mt-1">
              Please answer these questions to improve the requirement quality.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {questions.map((question, index) => (
            <div key={question.question_id} className="space-y-2">
              <label className="text-sm font-medium text-neutral-900">
                <span className="text-yellow-600 mr-2">{index + 1}.</span>
                {question.question}
              </label>
              <p className="text-xs text-neutral-600 ml-8 mb-2">
                Context: {question.context}
              </p>
              <textarea
                value={answers[question.question_id] || ''}
                onChange={(e) =>
                  handleAnswerChange(question.question_id, e.target.value)
                }
                placeholder="Provide your clarification..."
                className="input-base h-20 ml-8"
                disabled={isLoading}
              />
            </div>
          ))}

          {/* Submit Button */}
          <div className="flex gap-2 ml-8 pt-2">
            <button
              type="submit"
              disabled={!allQuestionsAnswered || isLoading}
              className="btn-primary flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              Submit Clarifications
            </button>
            <span className="text-xs text-neutral-600 self-center">
              {questions.length - Object.keys(answers).length} remaining
            </span>
          </div>
        </form>
      </div>
    </div>
  );
};
