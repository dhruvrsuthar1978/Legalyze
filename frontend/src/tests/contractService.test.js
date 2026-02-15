import { describe, it, expect } from 'vitest';
import { generationService } from '../services/generationService';

describe('generationService', () => {
  it('has adhocPreview function', () => {
    expect(typeof generationService.adhocPreview).toBe('function');
  });
});
