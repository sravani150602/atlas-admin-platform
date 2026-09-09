#ifndef ATLAS_POLICY_H
#define ATLAS_POLICY_H
#include <stddef.h>
/* Public ABI: roles viewer=0, operator=1, admin=2. Fail closed on bad input. */
typedef struct {
    int actor_role;
    int is_self;
    int target_role;
    int target_active;
    int active_admins;
    int action; /* suspend=0, restore=1, change_role=2 */
    int requested_role;
} atlas_request;
typedef struct {
    int allowed;
    int risk; /* low=0, medium=1, high=2 */
    char reason[160];
} atlas_decision;
int atlas_evaluate(const atlas_request *request, atlas_decision *decision);
int atlas_flight(const char *subject, const char *flag, unsigned int percent);
const char *atlas_version(void);
#endif
