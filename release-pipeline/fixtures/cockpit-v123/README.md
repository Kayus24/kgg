# Unreleased Cockpit v123 test support

`kgg_device_test_station.js` is an exact saved test-support copy from the private
v123 recovery snapshot (base `8077acbbb767ac6864aa1b2b5fedac26d5bbe291`, dirty source
`android-wrapper/app/src/preview/assets/android/kgg_device_test_station.js`).
SHA256: `2cda9b898ab9b8a78b9361352e672e165671737039d69d1a844db88faee120d6`.

The reported-scenarios browser test needs its collapsed-wrapper contract. Keeping
this fixture here preserves all 42 assertions without importing the unreleased
Android change into the product. It runs against the actual generated therapist
HTML. Wrapper results certify this synthetic fixture only, never an installed APK
or physical device. Existing dual-device synthetic fixtures still come from Main.
This file is not part of `parts.json` or an Android build.
