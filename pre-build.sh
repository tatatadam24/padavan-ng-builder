# script is run before the build
# zapret: ALT9 (Flowseal, no ts fooling) as default strategy, keep only strategy5,
# Flowseal lists into /usr/share/zapret/lists (subdir is not copied to /etc/storage)

Z=padavan-ng/trunk/user/zapret

die() { echo "::error::pre-build: $*"; exit 1; }

[ -d "$Z/config/strategy" ] || die "$Z/config/strategy not found"
[ -f "$Z/config/strategy/strategy5" ] || die "strategy5 not found"

find "$Z/config/strategy" -type f ! -name strategy5 -delete || die "unable to remove strategies"
cp -f custom/zapret/strategy "$Z/config/strategy/strategy" || die "unable to copy strategy"

mkdir -p "$Z/config/zapret/lists" "$Z/config/zapret/fake" || die "mkdir failed"
cp -f custom/zapret/lists/* "$Z/config/zapret/lists/" || die "unable to copy lists"
cp -f custom/zapret/fake/* "$Z/config/zapret/fake/" || die "unable to copy fakes"

find "$Z/config/strategy" "$Z/config/zapret/lists" -type f -exec sed -i 's|\r$||' {} + || die "dos2unix failed"

echo "zapret strategies:"; ls -l "$Z/config/strategy"
echo "zapret lists:"; ls -l "$Z/config/zapret/lists"
