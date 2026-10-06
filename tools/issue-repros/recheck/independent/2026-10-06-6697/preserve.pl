use strict;
use warnings;
use JSON::PP;
use Digest::SHA qw(sha256_hex);
use File::Find;
use Cwd qw(abs_path);
my $src = '<workspace>';
my $case = "$src/independent-verification/2026-10-06-6697-f39b054";
my $old = "$src/cleanup-issues/2026-10-04T155029+0900";
my $site = "$old/verification-tools/package-site";
my @files = (
    "$old/.build/slot-a/verification/rustpython",
    '<home>/.local/bin/python3',
    "$src/Lib/os.py", "$src/Lib/json/__init__.py", "$src/Lib/struct.py", "$src/Lib/importlib/metadata/__init__.py",
    "$src/crates/codegen/src/compile.rs", "$src/extra_tests/snippets/syntax_try.py", "$src/extra_tests/snippets/testutils.py",
    "$old/analysis/build-variants-a.json", "$old/logs/build-a/sqlite-verification-build.stdout", "$old/logs/build-a/sqlite-verification-build.stderr",
    "$old/.build/slot-a/verification/build/rustpython-vm-6e3530df589ea608/output",
    "$old/logs/build-b-3909b18e/provenance.json",
    glob("$old/logs/issue-6697-case-02/historical-3909b18eac-01.*"),
    "$old/repros/6697/issue-6697-case-02/source-01.py",
    glob("$src/cleanup-issues/6697-recheck-20261005T175703+0900/*.json"),
    "$src/cleanup-issues/6697-recheck-20261005T175703+0900/README.md",
    '<report-worktree>/tools/issue-repros/recheck/cases/4856/README.md',
    "$site/pygments/__init__.py", glob("$site/{pytest,pluggy,packaging,iniconfig,pygments}-*.dist-info/METADATA"),
);
for my $directory (qw(pytest _pytest pluggy packaging iniconfig)) {
    find({wanted => sub { push @files, $File::Find::name if -f $_; }, no_chdir => 1}, "$site/$directory");
}
my %hashes;
for my $path (@files) {
    open my $file, '<:raw', $path or die "$path: $!";
    local $/;
    $hashes{$path} = {sha256 => sha256_hex(<$file>), realpath => abs_path($path), bytes => -s $path};
}
my $stage = $ARGV[0];
die "invalid stage" unless $stage eq 'before' || $stage eq 'after';
my $output = "$case/evidence/preservation-$stage.json";
die "exists: $output" if -e $output;
open my $file, '>', $output or die $!;
print $file JSON::PP->new->utf8->canonical->pretty->encode(\%hashes);
print scalar(keys %hashes), " existing files hashed\n";
