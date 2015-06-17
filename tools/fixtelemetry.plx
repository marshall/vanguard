#!/usr/bin/perl
use strict;
use warnings;

my $log = 'var_log_upstart_vanguard.log';
my $output = 'telemetryoutput.json'; 
my $count = 1;
my $open = '[
    {
    "telemetry" : [ ';
my $close = '] } ]';
my $biglog = "../Downloads/var_log_upstart_vanguard.log";
my @lines;

open (LOG, "$biglog") or die "could not open $biglog for reading: $!\n";
while (<LOG>) { if (/telemetry:INFO/) { push @lines, $_; }  }
close LOG;

# `cat var_log_upstart_vanguard.log  | grep 'telemetry:INFO' | sed s/\\[telemetry:INFO\\]//g > $file `

# {\"free_mem\": 4364, \"int_temp\": 16.67024923021694, \"uptime\": 7491.07, \"cpu_usage\": 57, \"ext_temp\": -13.193173533505671}",

# In the log:
# { "time": "15:26:09,513", "free_mem": 402692, "int_temp": 17.40279872002276, "uptime": 25.63, "cpu_usage": 96, "ext_temp": -12.602965873456071},

# properly formatted:
# "{ \"time\": \"15:26:09,513\", \"free_mem\": 402692, \"int_temp\": 17.40279872002276, \"uptime\": 25.63, \"cpu_usage\": 96, \"ext_temp\": -12.602965873456071}",

open (OUT, ">$output") or die "could not open $output for writing; $!\n";
print OUT "$open\n";

my $filelength = scalar(@lines);
print "length of file is $filelength.\n";

foreach my $line(@lines) 
{
    chomp $line;
    $line =~ s/\r\n|\r|\n//g;
    $line =~ s/^\[\d\d\d\d-\d\d-\d\d (.*.?)\] \{/\{ "time": "$1", / ;
    $line =~ s/"/\\"/g;    
    print OUT "\t\"$line\"";

    if ($count < $filelength )
    {
#        print "Still not done. Count: $count\n";
        print OUT " ,\n";
    } else {
        print OUT " \n";
        print "Looks like we're done? Line count is $count and file line count is $filelength.\n";
        print OUT "$close \n";
        close OUT;
        exit;
    }
    $count++;
}

# EOF
