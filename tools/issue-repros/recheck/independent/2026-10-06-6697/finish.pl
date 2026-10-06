use strict;
use warnings;
use JSON::PP;
use Digest::SHA qw(sha256_hex);
my $src = '<workspace>';
my $case = "$src/independent-verification/2026-10-06-6697-f39b054";
sub bytes { my ($path) = @_; open my $f, '<:raw', $path or die "$path: $!"; local $/; return scalar(<$f>) // ''; }
sub json { return decode_json(bytes($_[0])); }
sub save { my ($name,$data) = @_; die "exists $name" if -e "$case/$name"; open my $f, '>', "$case/$name" or die $!; print $f JSON::PP->new->canonical->pretty->encode($data); }
my @order = qw(rp-version cp-version rp-identity cp-identity rp-version-v2 cp-version-v2 rp-identity-v2 cp-identity-v2 rp-original cp-original rp-call cp-call rp-controls cp-controls rp-pytest-probe cp-pytest-probe rp-syntax-try cp-syntax-try rp-pytest-smoke cp-pytest-smoke);
my @results;
for my $name (@order) {
    my $r = json("$case/records/$name.json");
    die "$name failed" unless $r->{exit_code} == 0 && !$r->{timeout};
    push @results, {id => $name, record => "records/$name.json", exit_code => $r->{exit_code}, timeout => $r->{timeout}, authoritative => $name =~ /^(rp|cp)-(version|identity)$/ ? JSON::PP::false : JSON::PP::true};
}
my $issue = json("$case/evidence/issue.json");
my $rp = json("$case/records/rp-identity-v2.stdout");
my $cp = json("$case/records/cp-identity-v2.stdout");
my $sources = json("$case/evidence/source-comparison.json");
my $preservation = json("$case/evidence/preservation-comparison.json");
die 'preservation changed' unless $preservation->{unchanged};
for my $path (keys %{$sources->{paths}}) { die "source differs $path" unless $sources->{paths}{$path}{equal}; }
my $readme = bytes("$case/README.md");
my @inline_inputs = qw(original.py call-original.py controls.py pytest-probe.py test_6697.py run-pytest.py pytest.ini);
for my $input (@inline_inputs) { die "missing exact inline input $input" unless index($readme, bytes("$case/inputs/$input")) >= 0; }
for my $name (qw(original call controls syntax-try pytest-probe)) {
    die "stdout differs $name" unless bytes("$case/records/rp-$name.stdout") eq bytes("$case/records/cp-$name.stdout");
    die "stderr not empty $name" unless bytes("$case/records/rp-$name.stderr") eq '' && bytes("$case/records/cp-$name.stderr") eq '';
}
die 'warning differs' unless bytes("$case/records/rp-pytest-smoke.stderr") eq bytes("$case/records/cp-pytest-smoke.stderr");
save('assessment.json', {
    issue => 6697, title => $issue->{title}, verdict => 'resolved', closure_recommended => JSON::PP::true,
    original_scope => 'Import-time SyntaxError caused by compiling comprehensions/nested scopes in finally blocks, observed while pytest.console_main imports _pytest.pytester; includes the exact commented function-definition reproducer.',
    verified_on_commit => 'f39b054b9c8cbbf884f53123eef028131789990c', verified_on_date => '2026-10-06',
    issue_state => {state => $issue->{state}, updated_at => $issue->{updated_at}, closed_at => $issue->{closed_at}, retrieved_at => '2026-10-06T02:34:52Z'},
    source_first_plan => 'SOURCE-FIRST-PLAN.md',
    platform => {os => 'macOS 26.5.2 (25F84), Darwin 25.5.0', architecture => 'arm64'},
    rustpython => {path => $rp->{executable}, realpath => $rp->{executable_realpath}, version => $rp->{version}, architecture => $rp->{machine}, sha256 => json("$case/records/rp-identity-v2.json")->{binary_sha256}, build_provenance => 'evidence/reused/build-variants-a.json', identity => 'records/rp-identity-v2.json'},
    cpython => {path => $cp->{executable}, realpath => $cp->{executable_realpath}, version => $cp->{version}, architecture => $cp->{machine}, sha256 => json("$case/records/cp-identity-v2.json")->{binary_sha256}, identity => 'records/cp-identity-v2.json'},
    packages => $rp->{packages}, results => \@results,
    checks => ['Exact reduced file compiles and defines the function without output', 'Exact function returns None', '12 comprehension/return/normal/exception controls preserve values and single finally execution', 'Current unmodified syntax_try.py passes on both interpreters', 'Complete installed pytester.py compiles and original console_main/HookRecorder imports succeed', 'Actual pytest_runtest_protocol generator preserves return value and computes exactly one controlled leak warning', 'Two tests pass through console_main on both interpreters'],
    expected_stderr => {pytest_smoke => 'Same PytestRemovedIn10Warning on both interpreters; console_main is deprecated.', other_authoritative_runs => 'empty'},
    historical => {reused => JSON::PP::true, rerun => JSON::PP::false, revision => '3909b18eac642d824cd5c1157f452e8765269a2e', exit_code => 1, same_input_sha256 => 'cc057db4113ba172a9ece7d32c64c29e3a04b2d088ad0a958680008c8510b95e', record => 'evidence/reused/historical-3909b18eac-01.json'},
    source_change => {url => 'https://github.com/RustPython/RustPython/pull/8507', commit => '2a793fcdd1461001a0078cc89d34833205f4f30b', ancestry_verified => JSON::PP::true, explanation => 'Save/restore nested symbol-table cursors while compiling extra finally-body copies on early exit.', baseline_followup => 'f87cfe7e7a additionally seeks to the finally body scope positions', first_fix_boundary_executed => JSON::PP::false},
    limits => ['Original pytest version, xonsh revision, dependency set, entrypoint and platform details were not provided; pytest 9.1.1 here is not an exact historical environment reconstruction.', 'Full xonsh suite and original rust-pytest launcher not executed.', 'Actual affected pytest method executed with controlled file lists, not native lsof integration.', 'Current executable build linkage relies on matching retained build records, fresh SHA256 and embedded banner; no rebuild or attestation of all historical build inputs.', 'No executed first-fix boundary; historical failure record is reused.', 'Targeted preservation hashes cover 147 selected pre-existing files, not every file on the machine.'],
    recording_correction => {superseded => ['rp-version', 'cp-version', 'rp-identity', 'cp-identity'], reason => 'Initial Perl recorder serialized empty stderr in list context; raw outputs preserved. Corrected run-v2.pl repeated identity/version probes with new names. All behavior runs used corrected recorder.'},
    preservation => $preservation, ai_assistance => 'OpenAI Codex',
});
save('provenance.json', {rustpython => $rp, cpython => $cp, source_comparison => $sources, preservation => $preservation, reused_build_record => 'evidence/reused/build-variants-a.json', build_provenance_limit => 'Historical records reused; matching fresh binary SHA256 and embedded version establish recorded artifact linkage, not a new reproducible-build attestation.'});
save('report-qa.json', {records_checked => scalar(@results), all_exit_zero => JSON::PP::true, all_no_timeout => JSON::PP::true, matching_output_pairs => [qw(original call controls syntax-try pytest-probe)], smoke_warning_equal => JSON::PP::true, exact_inline_inputs_checked => \@inline_inputs, preservation_unchanged => JSON::PP::true, selected_tracked_sources_equal_baseline => JSON::PP::true});
print "20 records checked; exact inline inputs, matching outputs, source equality, and preservation verified\n";
