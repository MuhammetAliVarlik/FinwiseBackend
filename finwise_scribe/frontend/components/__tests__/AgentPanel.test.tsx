import { render, screen } from '@testing-library/react';
import AgentPanel from '../AgentPanel';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';

describe('AgentPanel Component', () => {
  const baseProps = {
    messages: [],
    currentInput: '',
    isTyping: false,
    onInputChange: () => {},
    onSend: () => {},
    contextSymbol: 'AAPL',
  };

  it('renders header, context symbol, and input', () => {
    render(<AgentPanel {...baseProps} />);
    expect(screen.getByText(/Scribe Logic Engine/i)).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask Scribe about patterns/i)).toBeInTheDocument();
  });

  it('renders chat messages for user and agent roles', () => {
    render(
      <AgentPanel
        {...baseProps}
        messages={[
          { id: '1', role: 'user', content: 'What is the trend?', timestamp: '2026-01-01T00:00:00Z' },
          { id: '2', role: 'agent', content: 'Trend is bullish with moderate confidence.', timestamp: '2026-01-01T00:00:01Z' },
        ]}
      />
    );

    expect(screen.getByText(/What is the trend\?/i)).toBeInTheDocument();
    expect(screen.getByText(/Trend is bullish with moderate confidence\./i)).toBeInTheDocument();
  });

  it('disables send button while typing', () => {
    render(<AgentPanel {...baseProps} isTyping={true} currentInput="Hello" />);
    const sendButton = screen.getAllByRole('button').find((btn) => btn.hasAttribute('disabled'));
    expect(sendButton).toBeDefined();
    expect(sendButton).toBeDisabled();
  });
});