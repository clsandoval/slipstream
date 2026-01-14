import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VoiceIndicator } from '../VoiceIndicator';

describe('VoiceIndicator', () => {
  // Test 1: Shows status dot
  it('renders status dot', () => {
    render(<VoiceIndicator status="listening" />);
    expect(screen.getByTestId('voice-dot')).toBeInTheDocument();
  });

  // Test 2: Shows status text
  it('displays status text', () => {
    render(<VoiceIndicator status="listening" />);
    expect(screen.getByText('Listening')).toBeInTheDocument();
  });

  // Test 3: Dot color changes with status
  it('has correct color for listening', () => {
    render(<VoiceIndicator status="listening" />);
    const dot = screen.getByTestId('voice-dot');
    expect(dot).toHaveClass('bg-green-500');
  });

  // Test 4: Speaking status
  it('shows speaking status', () => {
    render(<VoiceIndicator status="speaking" />);
    expect(screen.getByText('Speaking')).toBeInTheDocument();
    expect(screen.getByTestId('voice-dot')).toHaveClass('bg-blue-500');
  });

  // Test 5: Idle status
  it('shows idle status', () => {
    render(<VoiceIndicator status="idle" />);
    expect(screen.getByTestId('voice-dot')).toHaveClass('bg-gray-500');
  });

  // Test 6: Dot pulses when active
  it('dot pulses when listening', () => {
    render(<VoiceIndicator status="listening" />);
    expect(screen.getByTestId('voice-dot')).toHaveClass('animate-pulse');
  });

  // Test 7: Dot pulses when speaking
  it('dot pulses when speaking', () => {
    render(<VoiceIndicator status="speaking" />);
    expect(screen.getByTestId('voice-dot')).toHaveClass('animate-pulse');
  });

  // Test 8: Dot does not pulse when idle
  it('dot does not pulse when idle', () => {
    render(<VoiceIndicator status="idle" />);
    expect(screen.getByTestId('voice-dot')).not.toHaveClass('animate-pulse');
  });
});
