#include "policy.h"
#include <stdint.h>
#include <stdio.h>

static int valid_role(int role) { return role >= 0 && role <= 2; }
static int deny(atlas_decision *out, const char *reason) {
    out->allowed = 0;
    (void)snprintf(out->reason, sizeof(out->reason), "%s", reason);
    return 0;
}
int atlas_evaluate(const atlas_request *r, atlas_decision *out) {
    if (out == NULL) return -1;
    *out = (atlas_decision){0};
    if (r == NULL) return deny(out, "Missing policy input");
    if (!valid_role(r->actor_role) || !valid_role(r->target_role) ||
        !valid_role(r->requested_role) || r->action < 0 || r->action > 2 ||
        r->active_admins < 0 || r->is_self < 0 || r->is_self > 1 ||
        r->target_active < 0 || r->target_active > 1)
        return deny(out, "Invalid policy input");
    out->risk = r->action == 2 || r->target_role == 2 ? 2 : 1;
    if (r->actor_role == 0) return deny(out, "Viewer accounts cannot change access");
    if (r->is_self) return deny(out, "Self changes require another administrator");
    if (r->actor_role == 1 && (r->target_role == 2 || r->action == 2))
        return deny(out, "Only administrators may change roles or manage administrators");
    if (r->target_role == 2 && r->target_active && r->active_admins <= 1 &&
        (r->action == 0 || (r->action == 2 && r->requested_role != 2)))
        return deny(out, "The last active administrator must be preserved");
    if ((r->action == 0 && !r->target_active) || (r->action == 1 && r->target_active) ||
        (r->action == 2 && r->target_role == r->requested_role))
        return deny(out, "This change would have no effect");
    out->allowed = 1;
    (void)snprintf(out->reason, sizeof(out->reason), "%s", "Policy permits this change; human confirmation is required");
    return 0;
}
static uint32_t hash_part(uint32_t hash, const char *text) {
    for (size_t i = 0; text[i] != '\0'; ++i) {
        hash ^= (unsigned char)text[i];
        hash *= UINT32_C(16777619);
    }
    return hash;
}
int atlas_flight(const char *subject, const char *flag, unsigned int percent) {
    if (!subject || !flag || percent > 100 || !subject[0] || !flag[0]) return 0;
    uint32_t hash = hash_part(UINT32_C(2166136261), flag);
    hash = hash_part(hash, ":");
    hash = hash_part(hash, subject);
    return (hash % 100) < percent;
}
const char *atlas_version(void) { return "1.0.0"; }
