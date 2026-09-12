import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import App from './App';

describe('ProjectLens App', () => {
  it('renders ProjectLens brand header', () => {
    render(<App />);
    const brand = screen.getByText(/ProjectLens/i);
    expect(brand).toBeDefined();
  });
});
