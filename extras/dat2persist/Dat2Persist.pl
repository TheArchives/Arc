#!/usr/bin/perl
################################################################
use strict;
use warnings;
################################################################
# INFORMATION: This is a hardcoded Perl converter for iCraft+.
# Dicts and ConfigParsers can actually be turned into other
# formats easily. THIS IS FOR REFERENCE ONLY!
################################################################
# Support functions
sub trim($){ # Trim whitespace
	my $string = shift;
	$string =~ s/^\s+//mg;
	$string =~ s/\s+$//mg;
	return $string;
}
################################################################
# Creates arrays of all Name->Balances
sub GetBalance {
	my ($Find) = @_;
	open(FH, "balances.dat");
	my @FileData = <FH>;
	close(FH);

	my %BalanceHash;
	my $FoundName = 0;
	my $Name = "";
	my $Amount = "";

	foreach $_ (@FileData) {
		$_ = trim($_);
		if(length($_) > 0){
			if($FoundName == 1 && $_ =~ /I(\d{1,})/){
				# OK we got a number
				$Amount = trim($1);
				$BalanceHash{$Name} = $Amount;
				$FoundName = 0;
			}elsif($_ =~ /'(\w{1,})'/){
				$Name = trim($1);
				$FoundName = 1;
			}
		}
	}
	return %BalanceHash;
}
################################################################
# Creates arrays of all Name->Titles
sub GetTitle {
	my ($Find) = @_;
	open(FH, "ranks.dat");
	my @FileData = <FH>;
	close(FH);

	my %TitleHash;
	my $FoundName = 0;
	my $Name = "";
	my $Title = "";

	foreach $_ (@FileData) {
		$_ = trim($_);
		if(length($_) > 0){
			if($FoundName == 1 && $_ =~ /'(.*)'/){
				$Title = trim($1);
				$FoundName = 0;
				$TitleHash{$Name} = $Title;
			}elsif($_ =~ /'(\w{1,})'/){
				$Name = trim($1);
				$FoundName = 1;
			}
		}
	}
	return %TitleHash;
}
################################################################
# This will print our header with info =)
sub PrintHeader {
	system("cls");
	print "Dat2Persist 1.0\n";
	print "Created by the blockBox team (Lead: UberFoX)\n";
	print "http://blockbox.hk-diy.net\n";
	print "\n";
	print "Please wait while we build the INI files.....\n";
}
################################################################
# The main parser it will read all the dats and create the INIs
sub Begin {
	# We need a persist folder so make it if it doesnt exist
	unless (-d "./persist"){
		mkdir("./persist");
	}
	# Display messages to user
	PrintHeader();
	# Get all data from lastseeen
	open(FH, "lastseen.meta");
	my @FileData = <FH>;
	close(FH);
	# User Data
	my $Name = "";
	my $LastVisit = "";
	my $Balance = "";
	my $Title = "";
	my $QuitMsg = "Goodbye.";
	my $Homeworld = "main";
	my $IP = "0.0.0.0";
	my $Count = @FileData;
	my $Current = 0;
	my $LastPrint = 0;
	# Now lets build some arrays
	my %BalanceHash = GetBalance(); # Create array of all balances
	my %TitleHash = GetTitle(); # Create array of all titles
	# Now lets find the user info and create the ini
	foreach $_ (@FileData) {
		my $line = trim($_);
		# Calculate percent of current finished
		my $Percent = int(($Current / $Count) * 100); # Convert to INT to remove decimals
		# We dont print the same percent twice (Since this would happen thousands of times)
		if($LastPrint != $Percent){
			$LastPrint = $Percent;
			PrintHeader();
			print "Completed $Percent%;\n";
		}
		if($line =~ /^(.{1,}) = (.{1,})$/){
			$Name = trim($1);
			$LastVisit = trim($2);
			$Balance = 0;
			if($BalanceHash{$Name}){
				$Balance = $BalanceHash{$Name};
			}
			$Title = "";
			if($TitleHash{$Name}){
				$Title = $TitleHash{$Name};
			}
			# Print the INI for this User
			open(FH, ">./persist/$Name.ini");
			print FH 	"[main]\n" .
						"lastseen = $LastVisit\n" .
						"ip = $IP\n" .
						"quitmsg = $QuitMsg\n" .
						"homeworld = $Homeworld\n" .
						"title = $Title\n" .
						"\n" .
						"[misc]\n" .
						"\n" .
						"[bank]\n" .
						"balance = $Balance\n";
			close(FH);
		}
		$Current++;
	}
	PrintHeader();
	print "Completed 100%\n";
	print "You may now move the persist folder under your server root directory.\n";
	print "Have fun using blockBox!\n";
	system("pause");
	exit;
}
################################################################
Begin(); # Run main funtion
################################################################