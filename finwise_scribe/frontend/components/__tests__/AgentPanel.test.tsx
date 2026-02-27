import { render, screen } from '@testing-library/react';
import AgentPanel from '../AgentPanel';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';

describe('AgentPanel Component', () => {
  it('renders the waiting state correctly when no data is provided', () => {
    render(<AgentPanel isLoading={false} response={null} />);
    expect(screen.getByText(/Awaiting Market Data/i)).toBeInTheDocument();
  });

  it('renders loading spinner when fetching', () => {
    render(<AgentPanel isLoading={true} response={null} />);
    expect(screen.getByText(/Generating Neuro-Symbolic Forecast/i)).toBeInTheDocument();
  });

  it('renders the LLM forecast when data is provided', () => {
    const mockResponse = {
      forecast: "The symbols S_UP_3 indicate strong bullish momentum.",
      confidence: 85
    };
    render(<AgentPanel isLoading={false} response={mockResponse} />);
    expect(screen.getByText(/S_UP_3 indicate strong/i)).toBeInTheDocument();
  });
});