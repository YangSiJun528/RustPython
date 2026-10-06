use strict;
use warnings;
my $path = '<6697-audit>/README.md';
open my $in, '<', $path or die $!;
my $text = do { local $/; <$in> };
close $in;
my $old = <<'OLD';
The following absolute paths are the ones used here. Set them to equivalent existing installations when reproducing elsewhere. `CASE` is this report directory; its inputs are provided verbatim below. No package install or build is needed.

```sh
SRC=<workspace>
CASE="$SRC/independent-verification/2026-10-06-6697-f39b054"
RP="$SRC/cleanup-issues/2026-10-04T155029+0900/.build/slot-a/verification/rustpython"
CP=<home>/.local/bin/python3
SITE="$SRC/cleanup-issues/2026-10-04T155029+0900/verification-tools/package-site"
export SRC CASE RP CP SITE
cd "$SRC"
OLD
my $new = <<'NEW';
Choose absolute paths and assign these shell variables before running the commands:

- `SRC`: existing RustPython source at the verified commit, including its matching `Lib`.
- `RP`: the existing RustPython executable for that commit.
- `CP`: an existing CPython 3.14.6 executable.
- `SITE`: the existing package directory containing pytest 9.1.1 and the versions listed above.
- `CASE`: a new writable reproduction directory; save the shown inputs under `CASE/inputs`.
- `TIMEOUT`: an existing GNU `timeout` executable. This audit used `/opt/homebrew/bin/timeout`.

The commands use `en_US.UTF-8`, available on the audited system. The exact original paths remain in the Environment section and raw records; no package install or build is part of these reproduction commands.

```sh
export SRC CASE RP CP SITE TIMEOUT
mkdir -p "$CASE/inputs" "$CASE/tmp"
cd "$SRC"
NEW
index($text, $old) >= 0 or die 'old setup not found';
$text =~ s/\Q$old\E/$new/;
$text =~ s/HOME=\/Users\/sijun-yang LC_ALL/HOME="\$HOME" LC_ALL/g;
$text =~ s/        \/opt\/homebrew\/bin\/timeout --signal/        "\$TIMEOUT" --signal/g;
open my $out, '>', $path or die $!;
print $out $text;
