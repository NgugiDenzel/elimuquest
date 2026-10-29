# Phase Six Security and Child-Data Privacy Review

**Review date:** 2026-10-29  
**Scope:** Local source-code and configuration review; not a penetration test, legal opinion,
or regulatory compliance assessment.

## Data and access observed

- The user profile stores email, full name, role, curriculum selection, timezone, daily XP
  goal, and account-active state.
- Learning activity is associated with users through lesson sessions, answer attempts,
  lesson progress, XP transactions, achievements, and daily activity.
- Learner endpoints require bearer authentication. Session lookup is scoped to the current
  user; lesson and subject queries are constrained to the user's selected curriculum and
  level.
- Passwords are hashed with `pwdlib`. Access tokens use HS256, an issuer, and an expiry.
  The local default lifetime is 60 minutes.
- Production configuration rejects the development JWT secret, the default SQLite URL,
  and non-HTTPS/local CORS origins.
- Local CORS defaults are explicit development origins, not a wildcard with credentials.
- The leaderboard API is authenticated and the interface says only first names and XP
  are shown. First names and learning activity are still identifying personal data,
  especially for children.

## Unresolved high-risk decisions

1. No privacy notice, terms/consent flow, parent or guardian workflow, account deletion
   endpoint, or documented retention schedule was found in the inspected learner and
   backend paths.
2. No rate-limiting control was found on registration or login. Add and test protection
   before external exposure.
3. There is no documented data-subject request, incident response, or support process.
4. A specialist must determine lawful basis, age/guardian requirements, data minimization,
   retention, access, deletion, and whether a first-name leaderboard is appropriate.
5. External service/data-sharing configuration and production operational controls were
   not verified.

The findings above are release blockers, not proof of a specific legal violation. No
account-deletion behavior was implemented in this phase because deletion scope and
retention obligations require an approved policy; deleting records ad hoc could destroy
learner history or conflict with required retention.

## Verification

The synthetic learner API check confirmed unauthenticated `/subjects` returns HTTP 401
and attempting to open a Grade 6 lesson while selected into Grade 9 returns HTTP 404.
Those are functional authorization checks, not a comprehensive access-control assessment.
The synthetic database began with no user or learner-activity records. The active
database was not used for test accounts or learner actions.

See the historical [Phase Five beta-readiness report](./PHASE_FIVE_BETA_READINESS.md)
for deployment blockers and the Phase Six
[learner journey results](./PHASE_SIX_LEARNER_JOURNEY_REPORT.md).
