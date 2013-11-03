#!/usr/bin/perl -w
# written by andrewt@cse.unsw.edu.au October 2013
# as a starting point for COMP2041 assignment 2
# http://www.cse.unsw.edu.au/~cs2041/assignments/mekong/

use CGI qw/:all/;

$debug = 0;
$| = 1;

if (!@ARGV) {
	# run as a CGI script
	cgi_main();
	
} else {
	# for debugging purposes run from the command line
	console_main();
}
exit 0;

# This is very simple CGI code that goes straight
# to the search screen and it doesn't format the
# search results at all

sub cgi_main {
	print page_header();
	
	set_global_variables();
	read_books($books_file);
	# Login parameters
	my $login = param('login');
	my $password = param('password');
	my $name = param('name');
	my $street = param('street');
	my $city = param('city');
	my $state = param('state');
	my $postcode = param('postcode');
	my $email = param('email');

	my $search_terms = param('search_terms');
	my $action = param('action');
	my $isbn = param('isbn');
	my $card_no = param('card_no');
	my $security_code = param('security_code');
	my $authenticated = 0;
	
	# check if logged in
	if (defined $login && defined $password){
		$authenticated = authenticate($login, $password);
	}



	# adding to basket
	if ($authenticated && defined $action && $action eq "Add to Cart"){
		$action = "Search";
		if (defined $isbn && legal_isbn($isbn)){
			add_basket($login, $isbn);
			print "<h6>Successfully added to cart!</h6>\n";
		}
	}

	# removing from basket
	if ($authenticated && defined $action && $action eq "Remove from Cart"){
		$action = "View Cart";
		if (defined $isbn && legal_isbn($isbn)){
			delete_basket($login, $isbn);
			print "<h6>Successfully deleted from Cart</h6>\n";
		}
	}

	# checking out
	if ($authenticated && defined $action && $action eq "Checked Out"){
		if (defined $card_no && legal_credit_card_number($card_no)){
			if (defined $security_code && legal_expiry_date($security_code)){
				finalize_order($login, $card_no, $security_code);
				print "<h6>Successfully checked out!</h6><br>\n";
				$action = "Search";
			} else {
				print "<h6>Invalid expirty date.</h6><br>\n";
				$action = "Check Out";
			}
		} else {
			print "<h6>Invalid credit card number (should be 16 digits, no other punctuation or spaces)</h6><br>\n";
			$action = "Check Out";
		}
	}

	# go to specific page
	# account creation
	if (defined $action && $action eq "Create Account"){
		if (defined $login && defined $password && defined $name && defined $street
			&& defined $city && defined $state && defined $postcode && defined $email){
			if (is_account_creatable($login, $password, $name, $street, $city, $state, $postcode, $email)){
				create_new_account($login, $password, $name, $street, $city, $state, $postcode, $email);
				print "<p>Account Created! <a href='mekong.cgi'>Click here to return to the main page and log in!</a>\n";
			} else {
				print "<p>$last_error</p>";
				print create_account_form();
			}
		} else {
			$last_error = "One or more fields not filled out. Please fill out all fields.";
			print "<p>$last_error</p>";
			print create_account_form();
		} 
	} elsif (defined $action && $action eq "Create New Account"){
		print create_account_form();

	# Basket
	} elsif ($authenticated && defined $action && $action eq "View Cart"){
		print logged_in_form($login, $password);
		my @inBasket = read_basket($login);
		if (@inBasket){
			print show_basket($login, $password, @inBasket);
			print "<br><form method='post'>
				<input type='hidden' name='login' value='$login'>
				<input type='hidden' name='password' value='$password'>
				<input class='btn' type='submit' name='action' value='Go Back'>\n";
			print "<form method='post'><input class='btn' type='submit' name='action' value='Check Out'></form>\n";
		} else {
			print "<br><h6>Cart is empty</h6>\n";
			print "<br><form method='post'><form method='post'><input type='hidden' name='login' value='$login'>
			<input type='hidden' name='password' value='$password'>
			<input class='btn' type='submit' name='action' value='Go Back'></form>\n";
		}

	# View Orders
	} elsif ($authenticated && defined $action && $action eq "View Orders"){
		print logged_in_form($login, $password);
		my @order_numbers = login_to_orders($login);
		if (@order_numbers){
			foreach my $order_num (@order_numbers){
				my @ordered_books = ();
				@ordered_books = read_order($order_num);
				my $time = localtime(shift(@ordered_books));
				my $card_no = shift(@ordered_books);
				my $expiry_date = shift(@ordered_books);
				print "<h6>Order #$order_num - $time</h6>";
				print "<h6>Card no: $card_no (Expiry $expiry_date )</h6>";
				print show_order(@ordered_books);
			}
			print "<br><form method='post'><input type='hidden' name='login' value='$login'>
				<input type='hidden' name='password' value='$password'>
				<input class='btn' type='submit' name='action' value='Go Back'></form>";

		} else {
			print "<br><h6>No Orders Made</h6>\n";
			print "<br><form method='post'><input type='hidden' name='login' value='$login'>
				<input type='hidden' name='password' value='$password'>
				<input class='btn' type='submit' name='action' value='Go Back'></form>";
		}

	# Checking Out
	} elsif ($authenticated && defined $action && $action eq "Check Out") {
		print logged_in_form($login, $password);
		my @inBasket = read_basket($login);
		if (@inBasket){
			print no_action_basket(@inBasket);
			print check_out_form($login, $password);
		} else {
			print "<br><h6>Can't check out, basket is empty.</h6>";
			print "<br><form method='post'><input type='hidden' name='login' value='$login'>
				<input type='hidden' name='password' value='$password'>
				<input class='btn' type='submit' name='action' value='Go Back'></form>";
		}
	# Searching
	} elsif ($authenticated && defined $search_terms){
		print logged_in_form($login, $password);
		print main_selections($login, $password);
		print search_results($search_terms, $login, $password);

	# Home page
	} elsif ($authenticated) {
		print logged_in_form($login, $password);
		print main_selections($login, $password);

	# Failed login
	} else {
		if (defined $login || defined $password){
			print "<p>$last_error</p>";
		}
		print login_form();
	}
	print page_trailer();
}

# simple login form without authentication	
sub login_form {
	return <<eof;
	<br>
	<br>
	<p>
	<form method="post">
	<label for="login">Username:</label>
	<input type="text" name="login" id="login"  width="20" />
	<label for="password">Password:</label>
	<input type="password" name="password" id="password"  width="20" />
 	<input class="btn" type="submit" name="action" value="Login">
  	<input class="btn" type="submit" name="action" value="Create New Account">
	</form>
	</p>
eof
}

sub logged_in_form {
	my ($login, $password) = @_;
	return <<eof;
	<form method="post">
	<input type="hidden" name="login" value="$login">
	<input type="hidden" name="password" value="$password">
	</form>
eof
}

sub check_out_form{
	my ($login, $password) = @_;
	my $toReturn = 
"<form method='post'>
<input type='hidden' name='login' value='$login'>
<input type='hidden' name='password' value='$password'>
<label for='card_no'>Credit Card Number:</label>
<input type='text' name='card_no' id='card_no' width='16' />
<label for='security_code'>Expiry Date:</label>
<input type='text' name='security_code' id='security_code' width='8' />
<button type='submit' name='action' value='Checked Out'>Check Out</button>
<input class='btn' type='submit' name='action' value='Go Back'></form>";
	return $toReturn;
}

sub create_account_form{
	return <<eof;
	<br>
	<br>
<form method="post">
	<label for="login">Username (3-8 characters):</label>
	<input type="text" name="login" id="login" width="10" />
	<label for="password">Password (At least 5 characters, no spaces):</label>
	<input type="password" name="password" id="password" width="10" />
	<label for="name">Full Name:</label>
	<input type="text" name="name" id="name" width="50" />
	<label for="street">Street Address:</label>
	<input type="text" name="street" id="address" width="50" />
	<label for="city">City:</label>
	<input type="text" name="city" id="city" width="25" />
	<label for="state">State:</label>
	<input type="text" name="state" id="state" width="25" />
	<label for="postcode">Postcode:</label>
	<input type="text" name="postcode" id="postcode" width="25" />
	<label for="email">Email:</label>
	<input type="text" name="email" id="email" width="35" />
	<input class="btn" type="submit" name="action" value="Create Account">
</form>
eof
}

# Returns false if not creatable for any reason, and sets $last_error to the reason
# Returns true if creatable
sub is_account_creatable{
	# A lot of this probably shouldn't be hard coded, but functionality is more important at the moment
	my ($login, $password, $name, $street, $city, $state, $postcode, $email) = @_;
	if (!legal_login($login)){
		return 0;
	}
	if (-r "$users_dir/$login") {
		$last_error = "Invalid user name: login already exists.\n";
		return 0;
	}
	if (!open(USER, ">$users_dir/$login")) {
		$last_error = "Can not create user file $users_dir/$login: $!\n";
		return 0;
	}
	close(USER);
	unlink "$users_dir/$login";
	if (!legal_password($password)) {
		return 0;
	} elsif (length($name) == 0 || length($street) == 0 || length($city) == 0 || 
			 length($state) == 0 || length($postcode) == 0 || length($email) == 0){
		$last_error = "One or more fields not filled out. Please fill out all fields.";
		return 0;
	} elsif (length($name) > 50){
		$last_error = "Name too long.\n";
		return 0;
	} elsif (length($street) > 50){
		$last_error = "Street name too long.\n";
		return 0;
	} elsif (length($city) > 25){
		$last_error = "City name too long.\n";
		return 0;
	} elsif (length($state)>25){
		$last_error = "State name too long.\n";
		return 0;
	} elsif (length($postcode)>25){
		$last_error = "Postcode too long.\n";
		return 0;
	} elsif (length($email)>35){
		$last_error = "Email address too long.\n";
		return 0;
	} elsif ($email !~ /.*@.*\..*/){
		$last_error = "Not a real email.\n";
		return 0;
	}

	return 1;
}

sub create_new_account{
	# should not be hard coded but is, will fix later if I have time
	my ($login, $password, $name, $street, $city, $state, $postcode, $email) = @_;
	open(USER, ">$users_dir/$login");
	print USER
	"password=$password\nname=$name\nstreet=$street\ncity=$street\nstate=$state\npostcode=$postcode\nemail=$email";
	close(USER);
}

# simple search form
sub main_selections{
	my ($login, $password) = @_;
	return <<eof;
	<p>
	<span>
	<form method="post" style="display:inline;">
		<input type='hidden' name='login' value='$login'>
		<input type='hidden' name='password' value='$password'>
		<label for="search">Search for a book:</label>
		<input type="text" name="search_terms" id="search" size=60>
		<input class="btn" type="submit" name="action" value="Search">
	 	<input class="btn" type="submit" name="action" value="View Cart">
	  	<input class="btn" type="submit" name="action" value="View Orders">
	</form>
	</span>
	<p>
eof
}

# ascii display of search results
sub search_results {
	my ($search_terms, $login, $password) = @_;
	my @matching_isbns = search_books($search_terms);
	# This code is repeated. It would be good to functionise it
	my $descriptions = get_book_descriptions(@matching_isbns);
	my @books = split /\n/, $descriptions;
	# "%s %7s %s - %s\n", $isbn, $book_details{$isbn}{price}, $title, $authors
	my $toReturn = "";
	$toReturn .= "<table>\n";
	$toReturn .= "  <tr>\n<th>Cover</th><th>ISBN</th><th>Price</th><th>Title</th><th>Author</th><th>Actions</th>\n</tr>";
	my $alt = 0;
	foreach my $book (@books){
		# Alternating colorus (set in CSS)
		if ($alt == 1){
			$toReturn .= "  <tr>\n";
			$alt = 0;
		} else {
			$toReturn .= "  <tr class=\"alt\">";
			$alt = 1;
		}
		my @thisBook = split /\t/, $book;
		my $image = 1;
		foreach my $detail (@thisBook){
			if ($image == 1){
				$toReturn .= "<td><img src=$detail></td>";
				$image = 0;
			} else {
				$toReturn .= "<td>$detail</td>";
			}
		}
		$toReturn.="<td><form method='post'><input type='hidden' name='isbn' value='$thisBook[1]'>
					<input type='hidden' name='login' value='$login'>
					<input type='hidden' name='password' value='$password'>
					<input type='hidden' name='search_terms' value='$search_terms'>
					<input class='btn' type='submit' name='action' value='Add to Cart'></form></td>\n";
		$toReturn .= "</tr>\n";
	}
	$toReturn .= "</table>\n";
	$toReturn .= "<p>";
	return $toReturn;
}

sub show_basket(@){
	my ($login, $password, @isbns) = @_;
	my $descriptions = get_book_descriptions(@isbns);
	my @books = split /\n/, $descriptions;
	# Currently same code as 
	my $toReturn .= "<table>\n";
	$toReturn .= "  <tr>\n<th>Cover</th><th>ISBN</th><th>Price</th><th>Title</th><th>Author</th><th>Actions</th>\n</tr>";
	my $alt = 0;
	foreach my $book (@books){
		# Alternating colorus (set in CSS)
		if ($alt == 1){
			$toReturn .= "  <tr>\n";
			$alt = 0;
		} else {
			$toReturn .= "  <tr class=\"alt\">";
			$alt = 1;
		}
		my @thisBook = split /\t/, $book;
		my $image = 1;
		foreach my $detail (@thisBook){
			if ($image == 1){
				$toReturn .= "<td><img src=$detail></td>";
				$image = 0;
			} else {
				$toReturn .= "<td>$detail</td>";
			}
		}
		$toReturn.="<td><form method='post'><input type='hidden' name='isbn' value='$thisBook[1]'>
					<input type='hidden' name='login' value='$login'>
					<input type='hidden' name='password' value='$password'>
					<input class='btn' type='submit' name='action' value='Remove from Cart'></form></td>\n";
		$toReturn .= "  </tr>\n";
	}
	$toReturn .= "</table>\n<br>";
	return $toReturn;
}

# This function exists because I'm lazy and needed a function to display the basket without actions
sub no_action_basket(@){
	my (@isbns) = @_;
	my $descriptions = get_book_descriptions(@isbns);
	my @books = split /\n/, $descriptions;
	# Currently same code as 
	my $toReturn .= "<table>\n";
	$toReturn .= "  <tr>\n<th>Cover</th><th>ISBN</th><th>Price</th><th>Title</th><th>Author</th>\n</tr>";
	my $alt = 0;
	foreach my $book (@books){
		# Alternating colorus (set in CSS)
		if ($alt == 1){
			$toReturn .= "  <tr>\n";
			$alt = 0;
		} else {
			$toReturn .= "  <tr class=\"alt\">";
			$alt = 1;
		}
		my @thisBook = split /\t/, $book;
		my $image = 1;
		foreach my $detail (@thisBook){
			if ($image == 1){
				$toReturn .= "<td><img src=$detail></td>";
				$image = 0;
			} else {
				$toReturn .= "<td>$detail</td>";
			}
		}
		$toReturn.="\n";
		$toReturn .= "  </tr>\n";
	}
	$toReturn .= "</table>\n<br>";
	return $toReturn;
}

sub show_order(@){
	my @isbns = @_;
	my $descriptions = get_book_descriptions(@isbns);
	my @books = split /\n/, $descriptions;
	# Currently same code as 
	my $toReturn .= "<table>\n";
	$toReturn .= "  <tr>\n<th>Cover</th><th>ISBN</th><th>Price</th><th>Title</th><th>Author</th>\n</tr>";
	my $alt = 0;
	foreach my $book (@books){
		# Alternating colorus (set in CSS)
		if ($alt == 1){
			$toReturn .= "  <tr>\n";
			$alt = 0;
		} else {
			$toReturn .= "  <tr class=\"alt\">";
			$alt = 1;
		}
		my @thisBook = split /\t/, $book;
		my $image = 1;
		foreach my $detail (@thisBook){
			if ($image == 1){
				$toReturn .= "<td><img src=$detail></td>";
				$image = 0;
			} else {
				$toReturn .= "<td>$detail</td>";
			}
		}
		$toReturn .= "\n";
		$toReturn .= "  </tr>\n";
	}
	$toReturn .= "</table>\n<br>";
	return $toReturn;
}

#
# HTML at top of every screen
#
sub page_header() {
	return <<eof;
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
<head>
<title>mekong.com.au</title>
<link rel="stylesheet" href="stylesheets/base.css">
<link rel="stylesheet" href="stylesheets/skeleton.css">
<link rel="stylesheet" href="stylesheets/layout.css">
</head>
<body>
<p>
<div class="container">
<h1>Mekong!<h2>
<h5>Buy some awesome books!</h5>
eof
}

#
# HTML at bottom of every screen
#
sub page_trailer() {
	#my $debugging_info = debugging_info();
	
	return <<eof;
	</div>
<body>
</html>
eof
}

#
# Print out information for debugging purposes
#
sub debugging_info() {
	my $params = "";
	foreach $p (param()) {
		$params .= "param($p)=".param($p)."\n"
	}

	return <<eof;
<hr>
<h4>Debugging information - parameter values supplied to $0</h4>
<pre>
$params
</pre>
<hr>
eof
}




###
### Below here are utility functions
### Most are unused by the code above, but you will 
### need to use these functions (or write your own equivalent functions)
### 
###

# return true if specified string can be used as a login

sub legal_login {
	my ($login) = @_;
	our ($last_error);

	if ($login !~ /^[a-zA-Z][a-zA-Z0-9]*$/) {
		$last_error = "Invalid login '$login': logins must start with a letter and contain only letters and digits.";
		return 0;
	}
	if (length $login < 3 || length $login > 8) {
		$last_error = "Invalid login: logins must be 3-8 characters long.";
		return 0;
	}
	return 1;
}

# return true if specified string can be used as a password

sub legal_password {
	my ($password) = @_;
	our ($last_error);
	
	if ($password =~ /\s/) {
		$last_error = "Invalid password: password can not contain white space.";
		return 0;
	}
	if (length $password < 5) {
		$last_error = "Invalid password: passwords must contain at least 5 characters.";
		return 0;
	}
	return 1;
}


# return true if specified string could be an ISBN

sub legal_isbn {
	my ($isbn) = @_;
	our ($last_error);
	
	return 1 if $isbn =~ /^\d{9}(\d|X)$/;
	$last_error = "Invalid isbn '$isbn' : an isbn must be exactly 10 digits.";
	return 0;
}


# return true if specified string could be an credit card number

sub legal_credit_card_number {
	my ($number) = @_;
	our ($last_error);
	
	return 1 if $number =~ /^\d{16}$/;
	$last_error = "Invalid credit card number - must be 16 digits.\n";
	return 0;
}

# return true if specified string could be an credit card expiry date

sub legal_expiry_date {
	my ($expiry_date) = @_;
	our ($last_error);
	
	return 1 if $expiry_date =~ /^\d\d\/\d\d$/;
	$last_error = "Invalid expiry date - must be mm/yy, e.g. 11/04.\n";
	return 0;
}


# return total cost of specified books

sub total_books {
	my @isbns = @_;
	our %book_details;
	$total = 0;
	foreach $isbn (@isbns) {
		die "Internal error: unknown isbn $isbn  in total_books" if !$book_details{$isbn}; # shouldn't happen
		my $price = $book_details{$isbn}{price};
		$price =~ s/[^0-9\.]//g;
		$total += $price;
	}
	return $total;
}

# return true if specified login & password are correct
# user's details are stored in hash user_details

sub authenticate {
	my ($login, $password) = @_;
	our (%user_details, $last_error);
	
	return 0 if !legal_login($login);
	if (!open(USER, "$users_dir/$login")) {
		$last_error = "User '$login' does not exist.";
		return 0;
	}
	my %details =();
	while (<USER>) {
		next if !/^([^=]+)=(.*)/;
		$details{$1} = $2;
	}
	close(USER);
	foreach $field (qw(name street city state postcode password)) {
		if (!defined $details{$field}) {
 	 	 	$last_error = "Incomplete user file: field $field missing";
			return 0;
		}
	}
	if ($details{"password"} ne $password) {
  	 	$last_error = "Incorrect password.";
		return 0;
	 }
	 %user_details = %details;
  	 return 1;
}

# read contents of files in the books dir into the hash book
# a list of field names in the order specified in the file
 
sub read_books {
	my ($books_file) = @_;
	our %book_details;
	print STDERR "read_books($books_file)\n" if $debug;
	open BOOKS, $books_file or die "Can not open books file '$books_file'\n";
	my $isbn;
	while (<BOOKS>) {
		if (/^\s*"(\d+X?)"\s*:\s*{\s*$/) {
			$isbn = $1;
			next;
		}
		next if !$isbn;
		my ($field, $value);
		if (($field, $value) = /^\s*"([^"]+)"\s*:\s*"(.*)",?\s*$/) {
			$attribute_names{$field}++;
			print STDERR "$isbn $field-> $value\n" if $debug > 1;
			$value =~ s/([^\\]|^)\\"/$1"/g;
	  		$book_details{$isbn}{$field} = $value;
		} elsif (($field) = /^\s*"([^"]+)"\s*:\s*\[\s*$/) {
			$attribute_names{$1}++;
			my @a = ();
			while (<BOOKS>) {
				last if /^\s*\]\s*,?\s*$/;
				push @a, $1 if /^\s*"(.*)"\s*,?\s*$/;
			}
	  		$value = join("\n", @a);
			$value =~ s/([^\\]|^)\\"/$1"/g;
	  		$book_details{$isbn}{$field} = $value;
	  		print STDERR "book{$isbn}{$field}=@a\n" if $debug > 1;
		}
	}
	close BOOKS;
}

# return books matching search string

sub search_books {
	my ($search_string) = @_;
	$search_string =~ s/\s*$//;
	$search_string =~ s/^\s*//;
	return search_books1(split /\s+/, $search_string);
}

# return books matching search terms

sub search_books1 {
	my (@search_terms) = @_;
	our %book_details;
	print STDERR "search_books1(@search_terms)\n" if $debug;
	my @unknown_fields = ();
	foreach $search_term (@search_terms) {
		push @unknown_fields, "'$1'" if $search_term =~ /([^:]+):/ && !$attribute_names{$1};
	}
	printf STDERR "$0: warning unknown field%s: @unknown_fields\n", (@unknown_fields > 1 ? 's' : '') if @unknown_fields;
	my @matches = ();
	BOOK: foreach $isbn (sort keys %book_details) {
		my $n_matches = 0;
		if (!$book_details{$isbn}{'=default_search='}) {
			$book_details{$isbn}{'=default_search='} = ($book_details{$isbn}{title} || '')."\n".($book_details{$isbn}{authors} || '');
			print STDERR "$isbn default_search -> '".$book_details{$isbn}{'=default_search='}."'\n" if $debug;
		}
		print STDERR "search_terms=@search_terms\n" if $debug > 1;
		foreach $search_term (@search_terms) {
			my $search_type = "=default_search=";
			my $term = $search_term;
			if ($search_term =~ /([^:]+):(.*)/) {
				$search_type = $1;
				$term = $2;
			}
			print STDERR "term=$term\n" if $debug > 1;
			while ($term =~ s/<([^">]*)"[^"]*"([^>]*)>/<$1 $2>/g) {}
			$term =~ s/<[^>]+>/ /g;
			next if $term !~ /\w/;
			$term =~ s/^\W+//g;
			$term =~ s/\W+$//g;
			$term =~ s/[^\w\n]+/\\b +\\b/g;
			$term =~ s/^/\\b/g;
			$term =~ s/$/\\b/g;
			next BOOK if !defined $book_details{$isbn}{$search_type};
			print STDERR "search_type=$search_type term=$term book=$book_details{$isbn}{$search_type}\n" if $debug;
			my $match;
			eval {
				my $field = $book_details{$isbn}{$search_type};
				# remove text that looks like HTML tags (not perfect)
				while ($field =~ s/<([^">]*)"[^"]*"([^>]*)>/<$1 $2>/g) {}
				$field =~ s/<[^>]+>/ /g;
				$field =~ s/[^\w\n]+/ /g;
				$match = $field !~ /$term/i;
			};
			if ($@) {
				$last_error = $@;
				$last_error =~ s/;.*//;
				return (); 
			}
			next BOOK if $match;
			$n_matches++;
		}
		push @matches, $isbn if $n_matches > 0;
	}
	
	sub bySalesRank {
		my $max_sales_rank = 100000000;
		my $s1 = $book_details{$a}{SalesRank} || $max_sales_rank;
		my $s2 = $book_details{$b}{SalesRank} || $max_sales_rank;
		return $a cmp $b if $s1 == $s2;
		return $s1 <=> $s2;
	}
	
	return sort bySalesRank @matches;
}


# return books in specified user's basket

sub read_basket {
	my ($login) = @_;
	our %book_details;
	open F, "$baskets_dir/$login" or return ();
	my @isbns = <F>;

	close(F);
	chomp(@isbns);
	!$book_details{$_} && die "Internal error: unknown isbn $_ in basket\n" foreach @isbns;
	return @isbns;
}


# delete specified book from specified user's basket
# only first occurance is deleted

sub delete_basket {
	my ($login, $delete_isbn) = @_;
	my @isbns = read_basket($login);
	open F, ">$baskets_dir/$login" or die "Can not open $baskets_dir/$login: $!";
	foreach $isbn (@isbns) {
		if ($isbn eq $delete_isbn) {
			$delete_isbn = "";
			next;
		}
		print F "$isbn\n";
	}
	close(F);
	unlink "$baskets_dir/$login" if ! -s "$baskets_dir/$login";
}


# add specified book to specified user's basket

sub add_basket {
	my ($login, $isbn) = @_;
	open F, ">>$baskets_dir/$login" or die "Can not open $baskets_dir/$login::$! \n";
	print F "$isbn\n";
	close(F);
}


# finalize specified order

sub finalize_order {
	my ($login, $credit_card_number, $expiry_date) = @_;
	my $order_number = 0;

	if (open ORDER_NUMBER, "$orders_dir/NEXT_ORDER_NUMBER") {
		$order_number = <ORDER_NUMBER>;
		chomp $order_number;
		close(ORDER_NUMBER);
	}
	$order_number++ while -r "$orders_dir/$order_number";
	open F, ">$orders_dir/NEXT_ORDER_NUMBER" or die "Can not open $orders_dir/NEXT_ORDER_NUMBER: $!\n";
	print F ($order_number + 1);
	close(F);

	my @basket_isbns = read_basket($login);
	open ORDER,">$orders_dir/$order_number" or die "Can not open $orders_dir/$order_number:$! \n";
	print ORDER "order_time=".time()."\n";
	print ORDER "credit_card_number=$credit_card_number\n";
	print ORDER "expiry_date=$expiry_date\n";
	print ORDER join("\n",@basket_isbns)."\n";
	close(ORDER);
	unlink "$baskets_dir/$login";
	
	open F, ">>$orders_dir/$login" or die "Can not open $orders_dir/$login:$! \n";
	print F "$order_number\n";
	close(F);
	
}


# return order numbers for specified login

sub login_to_orders {
	my ($login) = @_;
	open F, "$orders_dir/$login" or return ();
	@order_numbers = <F>;
	close(F);
	chomp(@order_numbers);
	return @order_numbers;
}



# return contents of specified order

sub read_order {
	my ($order_number) = @_;
	open F, "$orders_dir/$order_number" or warn "Can not open $orders_dir/$order_number:$! \n";
	@lines = <F>;
	close(F);
	chomp @lines;
	foreach (@lines[0..2]) {s/.*=//};
	return @lines;
}

###
### functions below are only for testing from the command line
### Your do not need to use these funtions
###

sub console_main {
	set_global_variables();
	$debug = 1;
	foreach $dir ($orders_dir,$baskets_dir,$users_dir) {
		if (! -d $dir) {
			print "Creating $dir\n";
			mkdir($dir, 0777) or die("Can not create $dir: $!");
		}
	}
	read_books($books_file);
	my @commands = qw(login new_account search details add drop basket checkout orders quit);
	my @commands_without_arguments = qw(basket checkout orders quit);
	my $login = "";
	
	print "mekong.com.au - ASCII interface\n";
	while (1) {
		$last_error = "";
		print "> ";
		$line = <STDIN> || last;
		$line =~ s/^\s*>\s*//;
		$line =~ /^\s*(\S+)\s*(.*)/ || next;
		($command, $argument) = ($1, $2);
		$command =~ tr/A-Z/a-z/;
		$argument = "" if !defined $argument;
		$argument =~ s/\s*$//;
		
		if (
			$command !~ /^[a-z_]+$/ ||
			!grep(/^$command$/, @commands) ||
			grep(/^$command$/, @commands_without_arguments) != ($argument eq "") ||
			($argument =~ /\s/ && $command ne "search")
		) {
			chomp $line;
			$line =~ s/\s*$//;
			$line =~ s/^\s*//;
			incorrect_command_message("$line");
			next;
		}

		if ($command eq "quit") {
			print "Thanks for shopping at mekong.com.au.\n";
			last;
		}
		if ($command eq "login") {
			$login = login_command($argument);
			next;
		} elsif ($command eq "new_account") {
			$login = new_account_command($argument);
			next;
		} elsif ($command eq "search") {
			search_command($argument);
			next;
		} elsif ($command eq "details") {
			details_command($argument);
			next;
		}
		
		if (!$login) {
			print "Not logged in.\n";
			next;
		}
		
		if ($command eq "basket") {
			basket_command($login);
		} elsif ($command eq "add") {
			add_command($login, $argument);
		} elsif ($command eq "drop") {
			drop_command($login, $argument);
		} elsif ($command eq "checkout") {
			checkout_command($login);
		} elsif ($command eq "orders") {
			orders_command($login);
		} else {
			warn "internal error: unexpected command $command";
		}
	}
}

sub login_command {
	my ($login) = @_;
	if (!legal_login($login)) {
		print "$last_error\n";
		return "";
	}
	if (!-r "$users_dir/$login") {
		print "User '$login' does not exist.\n";
		return "";
	}
	printf "Enter password: ";
	my $pass = <STDIN>;
	chomp $pass;
	if (!authenticate($login, $pass)) {
		print "$last_error\n";
		return "";
	}
	$login = $login;
	print "Welcome to mekong.com.au, $login.\n";
	return $login;
}

sub new_account_command {
	my ($login) = @_;
	if (!legal_login($login)) {
		print "$last_error\n";
		return "";
	}
	if (-r "$users_dir/$login") {
		print "Invalid user name: login already exists.\n";
		return "";
	}
	if (!open(USER, ">$users_dir/$login")) {
		print "Can not create user file $users_dir/$login: $!";
		return "";
	}
	foreach $description (@new_account_rows) {
		my ($name, $label)  = split /\|/, $description;
		next if $name eq "login";
		my $value;
		while (1) {
			print "$label ";
			$value = <STDIN>;
			exit 1 if !$value;
			chomp $value;
			if ($name eq "password" && !legal_password($value)) {
				print "$last_error\n";
				next;
			}
			last if $value =~ /\S+/;
		}
		$user_details{$name} = $value;
		print USER "$name=$value\n";
	}
	close(USER);
	print "Welcome to mekong.com.au, $login.\n";
	return $login;
}

sub search_command {
	my ($search_string) = @_;
	$search_string =~ s/\s*$//;
	$search_string =~ s/^\s*//;
	search_command1(split /\s+/, $search_string);
}

sub search_command1 {
	my (@search_terms) = @_;
	my @matching_isbns = search_books1(@search_terms);
	if ($last_error) {
		print "$last_error\n";
	} elsif (@matching_isbns) {
		print_books(@matching_isbns);
	} else {
		print "No books matched.\n";
	}
}

sub details_command {
	my ($isbn) = @_;
	our %book_details;
	if (!legal_isbn($isbn)) {
		print "$last_error\n";
		return;
	}
	if (!$book_details{$isbn}) {
		print "Unknown isbn: $isbn.\n";
		return;
	}
	print_books($isbn);
	foreach $attribute (sort keys %{$book_details{$isbn}}) {
		next if $attribute =~ /Image|=|^(|price|title|authors|productdescription)$/;
		print "$attribute: $book_details{$isbn}{$attribute}\n";
	}
	my $description = $book_details{$isbn}{productdescription} or return;
	$description =~ s/\s+/ /g;
	$description =~ s/\s*<p>\s*/\n\n/ig;
	while ($description =~ s/<([^">]*)"[^"]*"([^>]*)>/<$1 $2>/g) {}
	$description =~ s/(\s*)<[^>]+>(\s*)/$1 $2/g;
	$description =~ s/^\s*//g;
	$description =~ s/\s*$//g;
	print "$description\n";
}

sub basket_command {
	my ($login) = @_;
	my @basket_isbns = read_basket($login);
	if (!@basket_isbns) {
		print "Your shopping basket is empty.\n";
	} else {
		print_books(@basket_isbns);
		printf "Total: %11s\n", sprintf("\$%.2f", total_books(@basket_isbns));
	}
}

sub add_command {
	my ($login,$isbn) = @_;
	our %book_details;
	if (!legal_isbn($isbn)) {
		print "$last_error\n";
		return;
	}
	if (!$book_details{$isbn}) {
		print "Unknown isbn: $isbn.\n";
		return;
	}
	add_basket($login, $isbn);
}

sub drop_command {
	my ($login,$isbn) = @_;
	my @basket_isbns = read_basket($login);
	if (!legal_isbn($argument)) {
		print "$last_error\n";
		return;
	}
	if (!grep(/^$isbn$/, @basket_isbns)) {
		print "Isbn $isbn not in shopping basket.\n";
		return;
	}
	delete_basket($login, $isbn);
}

sub checkout_command {
	my ($login) = @_;
	my @basket_isbns = read_basket($login);
	if (!@basket_isbns) {
		print "Your shopping basket is empty.\n";
		return;
	}
	print "Shipping Details:\n$user_details{name}\n$user_details{street}\n$user_details{city}\n$user_details{state}, $user_details{postcode}\n\n";
	print_books(@basket_isbns);
	printf "Total: %11s\n", sprintf("\$%.2f", total_books(@basket_isbns));
	print "\n";
	my ($credit_card_number, $expiry_date);
	while (1) {
			print "Credit Card Number: ";
			$credit_card_number = <>;
			exit 1 if !$credit_card_number;
			$credit_card_number =~ s/\s//g;
			next if !$credit_card_number;
			last if $credit_card_number =~ /^\d{16}$/;
			last if legal_credit_card_number($credit_card_number);
			print "$last_error\n";
	}
	while (1) {
			print "Expiry date (mm/yy): ";
			$expiry_date = <>;
			exit 1 if !$expiry_date;
			$expiry_date =~ s/\s//g;
			next if !$expiry_date;
			last if legal_expiry_date($expiry_date);
			print "$last_error\n";
	}
	finalize_order($login, $credit_card_number, $expiry_date);
}

sub orders_command {
	my ($login) = @_;
	print "\n";
	foreach $order (login_to_orders($login)) {
		my ($order_time, $credit_card_number, $expiry_date, @isbns) = read_order($order);
		$order_time = localtime($order_time);
		print "Order #$order - $order_time\n";
		print "Credit Card Number: $credit_card_number (Expiry $expiry_date)\n";
		print_books(@isbns);
		print "\n";
	}
}

# print descriptions of specified books
sub print_books(@) {
	my @isbns = @_;
	print get_book_descriptions(@isbns);
}

# return descriptions of specified books
sub get_book_descriptions {
	my @isbns = @_;
	my $descriptions = "";
	our %book_details;
	foreach $isbn (@isbns) {
		die "Internal error: unknown isbn $isbn in print_books\n" if !$book_details{$isbn}; # shouldn't happen
		my $title = $book_details{$isbn}{title} || "";
		my $authors = $book_details{$isbn}{authors} || "";
		$authors =~ s/\n([^\n]*)$/ & $1/g;
		$authors =~ s/\n/, /g;
		$descriptions .= sprintf "%s\t%s\t%7s\t%s\t%s\n", $book_details{$isbn}{smallimageurl}, 
					  $isbn, $book_details{$isbn}{price}, $title, $authors;

	}
	return $descriptions;
}

sub set_global_variables {
	$base_dir = ".";
	$books_file = "$base_dir/books.json";
	$orders_dir = "$base_dir/orders";
	$baskets_dir = "$base_dir/baskets";
	$users_dir = "$base_dir/users";
	$last_error = "";
	%user_details = ();
	%book_details = ();
	%attribute_names = ();
	@new_account_rows = (
		  'login|Login:|10',
		  'password|Password:|10',
		  'name|Full Name:|50',
		  'street|Street:|50',
		  'city|City/Suburb:|25',
		  'state|State:|25',
		  'postcode|Postcode:|25',
		  'email|Email Address:|35'
		  );
}


sub incorrect_command_message {
	my ($command) = @_;
	print "Incorrect command: $command.\n";
	print <<eof;
Possible commands are:
login <login-name>
new_account <login-name>                    
search <words>
details <isbn>
add <isbn>
drop <isbn>
basket
checkout
orders
quit
eof
}

