# script is run before the build
# zapret: ALT9 (Flowseal) as default, "Router 5" (zapret2 strategy5) and all other Flowseal strategies,
# Flowseal lists into /usr/share/zapret/lists and fakes into /usr/share/zapret/fake/flowseal
# (subdirs are not copied to /etc/storage), web UI shows only these strategies

Z=padavan-ng/trunk/user/zapret

die() { echo "::error::pre-build: $*"; exit 1; }

[ -f "$Z/config/strategy2/strategy5" ] || die "zapret2 strategy5 not found"

find "$Z/config/strategy" -type f -delete || die "unable to remove zapret strategies"
find "$Z/config/strategy2" -type f ! -name strategy5 -delete || die "unable to remove zapret2 strategies"
cp -f custom/zapret/strategy "$Z/config/strategy/strategy" || die "unable to copy default strategy"
cp -f custom/zapret/strategies/strategy_* "$Z/config/strategy/" || die "unable to copy strategies"

mkdir -p "$Z/config/zapret/lists" "$Z/config/zapret/fake" || die "mkdir failed"
cp -f custom/zapret/lists/* "$Z/config/zapret/lists/" || die "unable to copy lists"
cp -rf custom/zapret/fake/. "$Z/config/zapret/fake/" || die "unable to copy fakes"

find "$Z/config/strategy" "$Z/config/zapret/lists" -type f -exec sed -i 's|\r$||' {} + || die "dos2unix failed"

python3 custom/patch_zapret.py || die "web UI / httpd / zapret.sh patch failed"

echo "zapret strategies:"; ls -l "$Z/config/strategy" "$Z/config/strategy2"
echo "zapret lists:"; ls -l "$Z/config/zapret/lists"
echo "zapret fakes:"; ls -lR "$Z/config/zapret/fake"
