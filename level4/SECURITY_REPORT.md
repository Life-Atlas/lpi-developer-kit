# Security Report

## Threats Considered

### 1. Prompt Injection
Handled by ignoring unsafe patterns.

### 2. Empty Input
Checked before processing.

### 3. Long Input
Can limit input size to prevent crashes.

### 4. System Crash
Handled using try-except blocks.

## Improvements
- Input validation
- Error handling
- Controlled agent communication
