# Hash Stability Report

Date: 2026-05-15

Code freeze baseline: `1ede6998bf442c22102b6a83530ef89a0cdadaaa`

Final acceptance commit: the docs/status-only commit that contains this report.

## Legacy Frozen Hashes

`strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

`strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

## Migrated v0.4 Reference Hashes

`kdj_cross_basic.qst.yaml` migrated to `qst-ir/0.4`:

- graph_hash: `sha256:34822b0de8b9b517c3b5cdb04f79adb2f9cd30ee63833891e62c204f6034411e`
- param_hash: `sha256:18f04bf380d53ad8020680f74c5686ba6dcf569543b4551b3b597f13aca6bb5c`
- instance_hash: `sha256:56fd90013048a81f9be6e2bc13adbf732c23f01c275a05ff598f6f9b9df67f25`

`examples_kdj_with_ema_filter.qst.yaml` migrated to `qst-ir/0.4`:

- graph_hash: `sha256:c4ac597df9553a45363832e1f9f919fb4948856dd5964191d5cdab7f2b058f8f`
- param_hash: `sha256:078d1dcccd7322b55efb91adf6485f0b868e07e4588ecc0564bea31200b487b0`
- instance_hash: `sha256:8fecad9fed31671da2ca8406a3ecebf0da7da2067865dbb9004807138f9d647b`

Migration target core registry hash:

- `sha256:29fcbdab8f69373aba522f93419e7477ee364ab10c4344e577b51df4ff8f4d4a`

## TokenPack Reference Hashes

- `qst-tokenpack-state-basic/0.1.0`: `sha256:8497ee4e2d8fb2dbcd22a4ee860446c8cf0ef9f39ccfe97d5ceca3f4cdcb0f36`
- `qst-tokenpack-state-fsm/0.1.0`: `sha256:72b81e92e0040fd8dcf280545f1093be7ff7ce61efeb6212204386a8d12a74af`
- `qst-tokenpack-decision-algebra/0.1.0`: `sha256:be5b1cc793331b9ff7082ea5207b91931dcafc732e5b694a927a8e7c11ffff9b`
- `qst-tokenpack-panel-ops/0.1.0`: `sha256:c3e2f7469477f7bc7e96a1159c74ab8568ca2c7f5187b6ec6a78d3cfcb7fcfb2`
- `qst-tokenpack-panel-weights/0.1.0`: `sha256:f0ade3cacbfb84f1237b3870d816de6e55339b2fe892ff8ae96df2a978810a2e`
- `qst-tokenpack-kalman/0.1.0`: `sha256:f561294104ed65fb3628f96d4427a8354f5a1540b1fe4e25b460bf46d4698fe4`

Custom Kalman TokenSpec:

- `my_pack.kalman_ema`: `sha256:f2e6fccb30591d4222863bf9c355cd2d2dbed17eb5057e38b46fb29595359efb`

## Expected Artifact Hash Evidence

Representative P-Validate artifacts:

- PV-A `state_cooldown` trace: `sha256:f9e3ba85328b9f5c7eafa7ca40426bc6e5ee029c1147680cd2a027f3b537425e`
- PV-A `state_cooldown` diagnostics: `sha256:acbafdd359c12b518959334828fac50cf7dfcbf14b6e3143c68fdff718f5ae24`
- PV-B `panel_top_bottom_market_neutral` trace: `sha256:13231b975370d110149a6c996b2d88e31c34967ce2c93a0fcc33f0e73087c95a`
- PV-B `panel_top_bottom_market_neutral` diagnostics: `sha256:bb89f8fa67fe9f3f75a9001edb5275f1906f2a8b476cb8e475d9b4bf87ec1edf`
- PV-C `temporal_shift_future.research` trace: `sha256:de782e9fe73579e0383b3c61b3f0ca0437cdf1a39cbd33612f246bdcf4c0bd15`
- PV-C `temporal_shift_future.research` diagnostics: `sha256:5ef9f26f8898f8c3f75199c1c2d8b600935326847bf0ee4d13d452a83a1dbc7a`
- PV-D `custom_token_kalman.research` trace: `sha256:0d305ba51aa410fb7a851a6d11cf70883c11f32a5a119c5d62ebb2049951ee33`
- PV-D `custom_token_kalman.research` diagnostics: `sha256:b8a126ed5692f5c1994b0e63ed3d46cb560cc5e978f0042cf5c331614a85344a`

Expected artifact hashes are computed over canonical artifact payloads excluding the `expected_artifact_hash` field itself.

## Hash Material Rules

Included semantic material:

- legacy graph/params/strategy content for legacy three-layer hashes.
- v0.4 graph, params, node signatures, token refs, and accepted semantic metadata.
- TypeSpec / PortSpec / temporal / numeric / lifecycle / risk metadata where included by the owning hash kind.
- TokenSpec and TokenPack canonical metadata.
- implementation and runtime environment references.
- audit semantic material excluding wall-clock timestamp.
- expected artifact semantic payload excluding its own hash.

Excluded non-semantic material:

- wall-clock timestamps in audit hash chains.
- `expected_artifact_hash` when computing expected artifact hashes.
- qstpkg approval records as portable trust.
- unrelated node metadata outside explicitly hash-bearing v0.4 semantic metadata.
- legacy provenance fields where accepted hash rules exclude them.

## Drift Policy

Any future drift in accepted legacy hashes, v0.4 identity hashes, TokenSpec/TokenPack hashes, schema capability meaning, or expected artifact hashes requires a new ADR or explicit correction work package.
