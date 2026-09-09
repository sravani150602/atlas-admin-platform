#include "policy.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
    atlas_request r = {2, 0, 0, 1, 1, 0, 0};
    atlas_decision d;
    assert(atlas_evaluate(&r, &d) == 0 && d.allowed);
    r.actor_role = 0; atlas_evaluate(&r, &d); assert(!d.allowed);
    r.actor_role = 2; r.is_self = 1; atlas_evaluate(&r, &d); assert(!d.allowed);
    r.is_self = 0; r.target_role = 2; atlas_evaluate(&r, &d); assert(!d.allowed);
    r.active_admins = 2; atlas_evaluate(&r, &d); assert(d.allowed && d.risk == 2);
    r.actor_role = 1; atlas_evaluate(&r, &d); assert(!d.allowed);
    r.target_role = 0; atlas_evaluate(&r, &d); assert(d.allowed);
    r.action = 2; r.requested_role = 2; atlas_evaluate(&r, &d); assert(!d.allowed);
    r.actor_role = 2; atlas_evaluate(&r, &d); assert(d.allowed);
    r.actor_role = 99; atlas_evaluate(&r, &d); assert(!d.allowed);
    atlas_evaluate(NULL, &d); assert(!d.allowed);
    assert(atlas_evaluate(&r, NULL) == -1);
    assert(atlas_flight("user", "ai", 100));
    assert(!atlas_flight("user", "ai", 0));
    assert(!atlas_flight(NULL, "ai", 50));
    assert(!atlas_flight("user", "ai", 101));
    int enabled = 0;
    for (int i = 0; i < 10000; ++i) {
        char subject[32]; snprintf(subject, sizeof(subject), "user-%d", i);
        int v = atlas_flight(subject, "ai", 25);
        assert(v == atlas_flight(subject, "ai", 25));
        enabled += v;
    }
    assert(enabled > 2000 && enabled < 3000);
    printf("C policy checks passed; 25%% cohort: %d/10000\n", enabled);
    return 0;
}
