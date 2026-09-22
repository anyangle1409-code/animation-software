# V5 contact-safe hand topology review

V5 is a separate candidate built on V4B. It refines the interior hand and finger surface without moving any original hand vertex, changing any original skin weight, or touching the frozen rig, grip logic, equipment locks, exercise definitions, production assets or `bundled.ts`.

## Change and reason

The inherited hands have coarse finger/wrist facets. V5 splits safe interior hand edges and interpolates the posed surface through the existing skinning. It adds 2,778 hand vertices and raises the body from 57,721 to 62,961 triangles, within the 50k–100k target. All 10,839 original body vertices and attributes match V4B exactly, including 1,852 original hand vertices. The worst discarded influence on any new vertex is 4.98%; none exceeds the 5% ceiling.

An unrestricted hand subdivision changed the push-up floor solution by 1.39 mm because the application finds the lowest hand vertex to solve floor contact. V5 protects 682 original hand vertices within 30 mm of the frozen floor-contact surface across four push-up poses and does not split any edge touching them. The fixed vertex list is in `reports/hand_contact_guard_v5.json`. This retains the original exercise mechanics; no runtime change is needed.

## Validation and visual limit

Six focused checks pass: shoulder sagittal profile; bare/dressed equivalence; grip contact and 343° wrap; renderer/exporter agreement; dumbbell/shorts clearance; and 26 frames each of curl, squat, shoulder press, push-up and pull-up. Original hand positions, 160 bone matrices and equipment transforms match the frozen dressed reference at every sampled frame. The existing push-up reach/flare findings remain. V4B's shoulder target and underarm measurements are unchanged. The body has no degenerate triangles or edges shared by more than two faces. The 400 pinned source files and all V4B deliverables match their recorded hashes. See `reports/final_integrity_v5_hands_curved.json`, `reports/weight_audit_v5_hands_curved.json`, `reports/v5_hands_curved_guards.log` and `reports/v5_hands_curved_exercise.log`.

`renders_v5_hands_curved/V5_HANDS_GRIP_AND_FLOOR_COMPARISON.jpg` compares matched curl, push-up and pull-up hand views with V4B; `V5_HANDS_ANATOMY_AND_EXERCISES.jpg` shows the five exercise peaks. The visible improvement is modest. This is a denser topology foundation for anatomical hand work, not a finished realistic finger sculpt. Palm creases, finger shape, thumb web and wrist transition still need deliberate modelling, with the floor-contact guard retained.
