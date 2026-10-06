use strict;
use warnings;
use JSON::PP;
use Digest::SHA qw(sha256_hex);
use Cwd qw(abs_path getcwd);
use Time::HiRes qw(time);
use POSIX qw(strftime);

my ($id, $kind, @args) = @ARGV;
die "usage: run.pl ID rp|cp ARGS\n" unless $id && ($kind eq 'rp' || $kind eq 'cp');
my $src = '<workspace>';
my $case = "$src/independent-verification/2026-10-06-6697-f39b054";
my $site = "$src/cleanup-issues/2026-10-04T155029+0900/verification-tools/package-site";
my $binary = $kind eq 'rp' ? "$src/cleanup-issues/2026-10-04T155029+0900/.build/slot-a/verification/rustpython" : '<home>/.local/bin/python3';
my %env = (
    PATH => '/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
    HOME => '<home>',
    LC_ALL => 'en_US.UTF-8',
    PYTHONDONTWRITEBYTECODE => '1',
    PYTEST_DISABLE_PLUGIN_AUTOLOAD => '1',
    PYTEST_ADDOPTS => '', PYTEST_PLUGINS => '',
    TMPDIR => "$case/tmp", SITE => $site, CASE => $case, SRC => $src,
);
if ($kind eq 'rp') { $env{RUSTPYTHONPATH} = "$src/Lib:$site"; }
else { $env{PYTHONPATH} = $site; }
my @argv = ($binary, '-B', '-S', @args);
my @wrapper = ('/opt/homebrew/bin/timeout', '--signal=TERM', '--kill-after=5s', '45s', @argv);
sub read_bytes { my ($p) = @_; open my $f, '<:raw', $p or die "$p: $!"; local $/; return scalar(<$f>) // ""; }
my %inputs;
for my $path ($0, @args, glob("$case/inputs/*"), "$site/_pytest/pytester.py", "$src/extra_tests/snippets/syntax_try.py", "$src/extra_tests/snippets/testutils.py") {
    next unless -f $path;
    $inputs{abs_path($path)} = sha256_hex(read_bytes($path));
}
my $stdout = "$case/records/$id.stdout";
my $stderr = "$case/records/$id.stderr";
die "record already exists" if -e $stdout || -e $stderr || -e "$case/records/$id.json";
my $start = time();
my $pid = fork();
die "fork: $!" unless defined $pid;
if ($pid == 0) {
    chdir $src or die $!;
    %ENV = %env;
    open STDIN, '<', '/dev/null' or die $!;
    open STDOUT, '>:raw', $stdout or die $!;
    open STDERR, '>:raw', $stderr or die $!;
    exec @wrapper;
    die "exec: $!";
}
waitpid($pid, 0);
my $wait = $?;
my $end = time();
my $record = {
    id => $id, kind => $kind, argv => \@argv, wrapper_argv => \@wrapper,
    cwd => $src, environment => \%env, environment_inheritance => JSON::PP::false,
    started_at_utc => strftime('%Y-%m-%dT%H:%M:%SZ', gmtime($start)),
    ended_at_utc => strftime('%Y-%m-%dT%H:%M:%SZ', gmtime($end)),
    elapsed_seconds => $end - $start, exit_code => $wait >> 8, signal => $wait & 127,
    timeout => (($wait >> 8) == 124 || ($wait >> 8) == 137) ? JSON::PP::true : JSON::PP::false,
    timeout_seconds => 45, kill_after_seconds => 5,
    binary_realpath => abs_path($binary), binary_sha256 => sha256_hex(read_bytes($binary)),
    inputs_sha256 => \%inputs, stdin => '/dev/null',
    stdout_path => $stdout, stderr_path => $stderr,
    stdout => read_bytes($stdout), stderr => read_bytes($stderr),
};
open my $record_file, '>', "$case/records/$id.json" or die $!;
print $record_file JSON::PP->new->utf8->canonical->pretty->encode($record);
close $record_file;
print "$id: exit $record->{exit_code}, elapsed $record->{elapsed_seconds}s\n";
print $record->{stdout}; print $record->{stderr};
