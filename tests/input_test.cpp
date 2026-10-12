#include "button_actions.h"
#include "play_effects.h"
#include "companion.h"
#include "life_tests.h"
int main() { return testButtonActions() && testPlayEffects() && testCompanion() && testLife() ? 0 : 1; }
