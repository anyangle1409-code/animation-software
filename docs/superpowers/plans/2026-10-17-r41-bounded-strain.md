# R41 — bounded strain redistribution from R40

R40 is numerically passing and owner visual review is still pending; it is immutable and is not promoted to production. Continue the original priorities2(stretch) and3(crushed shoulder triangles), preserving its straight outline/front fix. User authorized continuation. All canonical bones, production assets and non-S7 shape keys includingHGPT_SHOULDER remain untouched; owner photos stay outside the repo.

Diagnosis: R40 marked135.625degree frame has45 stretched triangles,33 touching existing local free support. Top166 has80 stretched triangles but existing5 editable controls have zero coefficients. The shoulder_press benchmark at t=.875 has crushed faces9030/21685, area ratios.056/.090, likewise zero coefficients on all5 editable controls. Earlier end-key freeze prevents any improvement at those poses.

R41 allows all7 existing S7controls110/120/130/136/145/156/166 to receive local material increments. Solver cap.70mm; actual saved-key change must<=.75mm after unchanged original Blender guards. This intentionally replaces R41's inherited exact end-key freeze with a small-update test because the end keys must influence top poses. The R40 exact-freeze test and saved candidate remain unchanged. All other preservation tests and original geometry gates remain unchanged; anchors remain exact. No large silhouette or skeleton change is authorized.

New fixed goals: marked stretch<=40(vs45), top stretch<=70(vs80), no crushed shoulder_press triangles(vs2). R40 reproduces all3 failures. Add smooth log-area quality energy while retaining all83 safety samples(82 paths plus exact130 front), line covectors, front-dihedral penalty and nativeBVH separation. Free support is limited to shoulder/armpit rest region and two adjacency rings; actual S7 change cap is independently checked before save.

Start with native export only and local feasibility check, then full independent native tests, immutable R41 build, matched R40/R41 images and press video. Never weaken new goals to make a trial pass. Report every regression.
