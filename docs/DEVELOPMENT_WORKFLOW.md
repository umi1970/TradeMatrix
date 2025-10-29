# Development Workflow - TradeMatrix.ai

**Last Updated:** 2025-10-24

---

## 🎯 Purpose

This document defines the **standard workflow** for developing new features in TradeMatrix.ai. Follow this process for every feature to ensure:
- Clear planning
- Structured implementation
- Comprehensive testing
- Documentation

---

## 📋 Feature Development Process

### Phase 1: Planning

1. **Create Feature Folder**
   ```bash
   mkdir -p docs/FEATURES/[feature-name]/
   ```

2. **Create Planning Documents**
   ```
   docs/FEATURES/[feature-name]/
   ├── 01-planning-document.md
   ├── 02-implementation-checklist.md
   ├── 03-testing-checklist.md
   ├── 04-technical-requirements.md
   └── README.md
   ```

3. **Fill Out Templates** (see below)

### Phase 2: Implementation

1. **Review Planning Documents**
   - Read `01-planning-document.md`
   - Follow `02-implementation-checklist.md` step-by-step

2. **Mark Progress**
   - Check off items in checklist as you complete them
   - Update status in README.md

3. **Code Standards**
   - TypeScript for frontend
   - Python type hints for backend
   - Write tests alongside code
   - Document complex logic

### Phase 3: Testing

1. **Follow Testing Checklist**
   - Work through `03-testing-checklist.md`
   - Unit tests
   - Integration tests
   - E2E tests (if applicable)
   - Manual testing

2. **Quality Checks**
   - Run linters
   - Run type checks
   - Run all tests
   - Check accessibility

### Phase 4: Documentation

1. **Update Documentation**
   - API docs (if applicable)
   - User-facing docs
   - Code comments
   - README updates

2. **Complete Feature README**
   - Mark as complete
   - Add deployment notes
   - Document any known issues

---

## 📄 Document Templates

### 1. `01-planning-document.md`

```markdown
# [Feature Name] - Planning Document

## Overview
Brief description of what this feature does and why it's needed.

## Goals
- [ ] Goal 1
- [ ] Goal 2

## User Stories
1. As a [user type], I want [goal] so that [benefit]

## Requirements

### Functional Requirements
- Requirement 1
- Requirement 2

### Non-Functional Requirements
- Performance targets
- Security considerations
- Accessibility requirements

## Design Decisions
- Decision 1: Why we chose X over Y
- Decision 2: ...

## Dependencies
- External APIs
- Libraries
- Other features

## Out of Scope
What this feature will NOT include (for now)

## Timeline Estimate
Estimated development time: X days/weeks
```

### 2. `02-implementation-checklist.md`

```markdown
# [Feature Name] - Implementation Checklist

## Status: 🚧 In Progress / ✅ Complete

---

## Backend

### Database
- [ ] Create database models
- [ ] Create migrations
- [ ] Add indexes
- [ ] Update schema docs

### API
- [ ] Create API endpoints
- [ ] Add request validation
- [ ] Add response schemas
- [ ] Implement error handling
- [ ] Add authentication/authorization

### Business Logic
- [ ] Implement core logic
- [ ] Add validation
- [ ] Handle edge cases
- [ ] Add logging

---

## Frontend

### Components
- [ ] Create UI components
- [ ] Add TypeScript types
- [ ] Implement state management
- [ ] Add error boundaries

### Pages
- [ ] Create/update pages
- [ ] Add routing
- [ ] Implement data fetching
- [ ] Add loading states

### Styling
- [ ] Apply design system colors
- [ ] Ensure responsive design
- [ ] Add dark mode support (if applicable)

---

## Integration
- [ ] Connect frontend to backend
- [ ] Test API integration
- [ ] Handle errors gracefully
- [ ] Add loading indicators

---

## Documentation
- [ ] Update API docs
- [ ] Add code comments
- [ ] Update README
- [ ] Add usage examples
```

### 3. `03-testing-checklist.md`

```markdown
# [Feature Name] - Testing Checklist

## Status: 🚧 In Progress / ✅ Complete

---

## Unit Tests

### Backend
- [ ] Test model methods
- [ ] Test API endpoints
- [ ] Test business logic
- [ ] Test error handling
- [ ] Test edge cases

### Frontend
- [ ] Test components
- [ ] Test hooks
- [ ] Test utilities
- [ ] Test error states

---

## Integration Tests
- [ ] Test API integration
- [ ] Test database operations
- [ ] Test external API calls
- [ ] Test background jobs (if applicable)

---

## E2E Tests
- [ ] Test happy path
- [ ] Test error scenarios
- [ ] Test edge cases

---

## Manual Testing

### Functionality
- [ ] Feature works as expected
- [ ] All buttons/links work
- [ ] Forms validate correctly
- [ ] Error messages are clear

### UI/UX
- [ ] Responsive on mobile
- [ ] Responsive on tablet
- [ ] Responsive on desktop
- [ ] Colors match design system
- [ ] Animations smooth

### Performance
- [ ] Page loads quickly
- [ ] No console errors
- [ ] No memory leaks

### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader friendly
- [ ] ARIA labels present
- [ ] Color contrast sufficient

---

## Browser Testing
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

---

## Security
- [ ] Input sanitization
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection (if applicable)
```

### 4. `04-technical-requirements.md`

```markdown
# [Feature Name] - Technical Requirements

## Stack

### Frontend
- Framework: Next.js 16
- Language: TypeScript
- Styling: Tailwind CSS
- Libraries: [List specific libraries]

### Backend
- Framework: FastAPI
- Language: Python 3.11+
- Database: PostgreSQL
- Libraries: [List specific libraries]

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/...` | ... | Required |
| POST | `/api/...` | ... | Required |

---

## Database Schema

### Tables
```sql
CREATE TABLE example (
  id UUID PRIMARY KEY,
  ...
);
```

### Relationships
- Table A → Table B (one-to-many)

---

## External APIs
- API 1: Purpose, rate limits
- API 2: Purpose, rate limits

---

## Environment Variables
```env
NEXT_PUBLIC_API_URL=...
OPENAI_API_KEY=...
```

---

## Performance Targets
- Page load: < 2s
- API response: < 500ms
- Database query: < 100ms

---

## Security Considerations
- Authentication method
- Authorization rules
- Data encryption
- Rate limiting
```

### 5. `README.md`

```markdown
# [Feature Name]

**Status:** 🚧 In Progress / ✅ Complete
**Priority:** High / Medium / Low
**Started:** YYYY-MM-DD
**Completed:** YYYY-MM-DD

---

## Quick Overview
One-sentence description of what this feature does.

## Documents
- [Planning](./01-planning-document.md)
- [Implementation Checklist](./02-implementation-checklist.md)
- [Testing Checklist](./03-testing-checklist.md)
- [Technical Requirements](./04-technical-requirements.md)

## Progress
- Planning: ✅ Complete
- Implementation: 🚧 In Progress (60%)
- Testing: ⏸️ Pending
- Documentation: ⏸️ Pending

## Notes
- Any important decisions made during development
- Blockers encountered
- Changes from original plan
```

---

## 🤖 For Claude (AI Assistant)

### When Starting a New Session

**ALWAYS do this first:**

1. ✅ Read `/docs/PROJECT_OVERVIEW.md`
2. ✅ Read `/docs/DEVELOPMENT_WORKFLOW.md` (this file)
3. ✅ Check `/docs/FEATURES/` for current features
4. ✅ Look for checklists marked 🚧 In Progress

### When Implementing a Feature

1. ✅ Read ALL planning documents first
2. ✅ Follow implementation checklist **step by step**
3. ✅ Mark items as complete in the checklist as you go
4. ✅ Run tests after each major change
5. ✅ Update README with progress
6. ✅ Document any deviations from the plan

### Checklist Update Format

When marking items complete:
```markdown
- [x] Item completed ✅
- [ ] Item in progress 🚧
- [ ] Item pending ⏸️
```

---

## 🎯 Quick Commands

```bash
# Create new feature folder
mkdir -p docs/FEATURES/[feature-name]

# Copy templates
cp docs/FEATURES/_template/* docs/FEATURES/[feature-name]/

# Start development
cd apps/web && npm run dev

# Run tests
npm run test

# Commit changes
git add .
git commit -m "feat(feature-name): description"
git push -u origin claude/init-saas-project-011CUS1no4jgfoELpLgTnhch
```

---

## 📌 Remember

- **One feature = One folder** in `docs/FEATURES/`
- **Always use checklists** - they prevent missing steps
- **Test as you go** - don't wait until the end
- **Document decisions** - future you will thank you
- **Update status** - keep README current

---

**Happy coding! 🚀**
