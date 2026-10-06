use strict;
use warnings;
use JSON::PP;
use Digest::SHA qw(sha256_hex);
my $src = '<workspace>';
my $case = "$src/independent-verification/2026-10-06-6697-f39b054";
my $old = "$src/cleanup-issues/2026-10-04T155029+0900";
sub bytes { my ($p) = @_; open my $f, '<:raw', $p or die $!; local $/; return scalar(<$f>) // ''; }
my %sources = (
    'build-variants-a.json' => "$old/analysis/build-variants-a.json",
    'sqlite-verification-build.stdout' => "$old/logs/build-a/sqlite-verification-build.stdout",
    'sqlite-verification-build.stderr' => "$old/logs/build-a/sqlite-verification-build.stderr",
    'rustpython-vm-build-output.txt' => "$old/.build/slot-a/verification/build/rustpython-vm-6e3530df589ea608/output",
    'historical-3909b18eac-01.json' => "$old/logs/issue-6697-case-02/historical-3909b18eac-01.json",
    'historical-3909b18eac-01.stdout' => "$old/logs/issue-6697-case-02/historical-3909b18eac-01.stdout",
    'historical-3909b18eac-01.stderr' => "$old/logs/issue-6697-case-02/historical-3909b18eac-01.stderr",
    'historical-source-01.py' => "$old/repros/6697/issue-6697-case-02/source-01.py",
    'historical-build-provenance.json' => "$old/logs/build-b-3909b18e/provenance.json",
    'syntax_try.py' => "$src/extra_tests/snippets/syntax_try.py",
    'testutils.py' => "$src/extra_tests/snippets/testutils.py",
    'pytester.py' => "$old/verification-tools/package-site/_pytest/pytester.py",
);
my %copies;
for my $name (sort keys %sources) {
    my $original_hash = sha256_hex(bytes($sources{$name}));
    my $copy = "evidence/reused/$name";
    my $copy_hash = sha256_hex(bytes("$case/$copy"));
    die "copy differs $name" unless $original_hash eq $copy_hash;
    $copies{$copy} = {original_path => $sources{$name}, original_sha256 => $original_hash, copy_sha256 => $copy_hash, verbatim_copy => JSON::PP::true};
}
open my $out, '>', "$case/evidence/reused-map.json" or die $!;
print $out JSON::PP->new->canonical->pretty->encode(\%copies);
my $readme = bytes("$case/README.md");
my @inputs = qw(original.py call-original.py controls.py pytest-probe.py test_6697.py run-pytest.py pytest.ini);
for my $input (@inputs) { die "missing inline input" unless index($readme, bytes("$case/inputs/$input")) >= 0; }
my @missing;
my $prose = $readme;
$prose =~ s/```.*?```//sg;
while ($prose =~ /\]\(([^)]+)\)/g) {
    my $target = $1;
    next if $target =~ /^https?:/;
    push @missing, $target unless -e "$case/$target";
}
die "missing links @missing" if @missing;
open my $qa, '>', "$case/evidence/final-document-check.json" or die $!;
print $qa JSON::PP->new->canonical->pretty->encode({readme_sha256 => sha256_hex($readme), assessment_sha256 => sha256_hex(bytes("$case/assessment.json")), exact_inline_inputs => \@inputs, local_links_exist => JSON::PP::true, reused_copies_checked => scalar(keys %copies), new_behavior_runs_after_document_edit => JSON::PP::false});
print "Final README: exact inputs and links checked; 12 reused copies match originals\n";
