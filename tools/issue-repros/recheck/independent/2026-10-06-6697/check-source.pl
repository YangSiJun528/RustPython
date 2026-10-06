use strict;
use warnings;
use Digest::SHA qw(sha256_hex);
use JSON::PP;
my $base = 'f39b054b9c8cbbf884f53123eef028131789990c';
my $case = '<6697-audit>';
open my $paths, '<', "$case/evidence/tracked-paths.txt" or die $!;
my @paths = <$paths>;
my %result;
for my $path (@paths) {
    chomp $path;
    open my $file, '<:raw', $path or die $!;
    my $working = do { local $/; <$file> };
    open my $git, '-|', 'git', 'show', "$base:$path" or die $!;
    my $baseline = do { local $/; <$git> };
    close $git or die "git show $path failed";
    $result{$path} = {working_sha256 => sha256_hex($working), baseline_sha256 => sha256_hex($baseline), equal => $working eq $baseline ? JSON::PP::true : JSON::PP::false};
}
my @ancestry = ('git', 'merge-base', '--is-ancestor', '2a793fcdd1461001a0078cc89d34833205f4f30b', $base);
system @ancestry;
my $ancestry_exit = $? >> 8;
open my $out, '>', "$case/evidence/source-comparison.json" or die $!;
print $out JSON::PP->new->canonical->pretty->encode({baseline => $base, paths => \%result, source_change_ancestry => {argv => \@ancestry, exit_code => $ancestry_exit}});
