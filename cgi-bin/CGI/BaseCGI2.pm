=pod

=head1 NAME

CGI::BaseCGI - Manage any CGI scripts

=head1 SYNOPSIS

my $base_cgi = CGI::BaseCGI -> new();

=head1 REQUIRES

CGI
CGI::Session
File::Copy

=head1 DESCRIPTION

This package enable to display a lot of common functions of CGI scripts

=cut

package CGI::BaseCGI2;

use strict;
use Carp qw (cluck confess croak);
use warnings;
use CGI::Session;
use File::Copy;
use Template;

use CGI qw(-private_tempfiles :standard);
use vars qw($fu);

use Config::Configuration;

use base qw(CGI);



# Script global constants
####################

=pod

=head1 CONSTANTS

B<HOME_DIR>:  String, public

                   used to define the home directory of the web server

B<WEB_DIR>:  String, public

                   used to define the URL of the web server

=cut

my $WEB_DIR = $Configuration::WEB_DIR;
my $HOME_DIR = $Configuration::HOME_DIR;

# Script global variables
##########################

=pod

=head1 VARIABLES

B<cgi>:  String, public

                   the CGI

=cut


# Package subs
###############

=pod

=head1 STATIC METHODS

=head2 CONSTRUCTOR

B<Description>       : Creates a new instance.

B<ArgsCount>         : 0

B<Return>            : CGI::BaseCGI, a new instance.

B<Caller>            : general

B<Exception>         :

B<Example>           :

=cut

sub new
{
    my ($proto) = @_;
    my $class = ref($proto) || $proto;
    my $self = $class->SUPER::new();
    bless($self, $class);

    $self->{SESSION}        = undef;
    $self->{SESSION_COOKIE} = undef;

    # init session info
    CGI::Session->name('CGISESSID');
    $self->{SESSION} = new CGI::Session("driver:File", $self, {'Directory' => "/tmp"});
    # update expiration according to account type
    if ($self->{SESSION}->param("is_admin"))
    {
        # admin account
        $self->{SESSION}->expire('+2h');
    }
    else
    {
        # user account
        $self->{SESSION}->expire('+5h');
    }
    
    # check if session cookie is valid
    my $cookie = $self->cookie(-name => 'CGISESSID');
    if ((not $cookie) || ($self->{SESSION}->id() ne $cookie))
    {
        # reset session cookie
        $self->{SESSION_COOKIE} = $self->cookie(
                                      -name    => 'CGISESSID',
                                      -value   => $self->{SESSION}->id(),
                                      -path    => "/"
                                               );
    }
    elsif ($cookie && ($self->{SESSION}->id() eq $cookie))
    {
        # reset cookie expiration
        $self->{SESSION_COOKIE} = $self->cookie(
                                      -name    => 'CGISESSID',
                                      -value   => $self->{SESSION}->id(),
                                      -expires => '+24h',
                                      -path    => "/"
                                               );
    }
    return $self;
}

=pod

=head1 ACCESSORS

=cut


=pod

=head2 setTitle

B<Description>: set the title of the web page

B<ArgsCount>  : 1

=over 4

=item arg    : String

=back

B<Return>     :  void

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub setTitle
{
    my ($self, $value) = @_;
    $self -> {TITLE} = $value;
}



=head2 getTitle

B<Description>: get the title of the web page

B<ArgsCount>  : 0

B<Return>     : String

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub getTitle
{
    my ($self) = @_;
   return $self -> {TITLE};
}

=pod

=head2 getSection

B<Description>: get the section for tab menu

B<ArgsCount>  : 0

B<Return>     : String

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub getSection
{
    my ($self) = @_;
   return $self -> {SECTION};
}

=pod

=head2 setSection

B<Description>: set the section for tab menu

B<ArgsCount>  : 1

=over 4

=item arg    : String

=back

B<Return>     :  void

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub setSection
{
    my ($self, $value) = @_;
    $self -> {SECTION} = $value;
}


=pod

=head2 getRefreshing

B<Description>: get the refreshing link

B<ArgsCount>  : 0

B<Return>     : String

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub getRefreshing
{
    my ($self) = @_;
   return $self -> {REFRESHING};
}

=pod

=head2 setRefreshing

B<Description>: set the refreshing link

B<ArgsCount>  : 1

=over 4

=item arg    : String

=back

B<Return>     :  void

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub setRefreshing
{
    my ($self, $value) = @_;
    $self -> {REFRESHING} = $value;
}



=head2 getHeading

B<Description>: get the heading of the web page

B<ArgsCount>  : 0

B<Return>     : String

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub getHeading
{
    my ($self) = @_;
   return $self -> {HEADING};
}

=pod

=head2 setHeading

B<Description>: set the heading of the web page

B<ArgsCount>  : 1

=over 4

=item arg    : String

=back

B<Return>     :  void

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub setHeading
{
    my ($self, $value) = @_;
    $self -> {HEADING} = $value;
}


=pod

=head1 METHODS

=cut


#############################################################################################################################################################
#
#                                                                  head HTML
#
#############################################################################################################################################################

=pod

=head2 headHTML

B<Description>       : displays the head of the web page with lab logos

B<ArgsCount>         : 0

B<Return>            : void

B<Exception>         :

=cut

sub headHTML($$$$)
  {
    my $self = shift;
    my $section = $_[0];
    my $refreshing = $_[1];
    my $time_reloading = $_[2];
    my $use_highcharts = $_[3];
    my $style= "$Configuration::STYLE_DIR/style.css";
    my $menu_style= "$Configuration::STYLE_DIR/menu.css";
    my $onglet_style= "$Configuration::STYLE_DIR/onglets.css";
    my $results_style = "$Configuration::STYLE_DIR/results.css";
    

    my $title = $self -> getTitle();
    my $heading = $self -> getHeading();
    if ($refreshing)
      {
		print $self -> header(-refresh=>"$time_reloading; URL=$refreshing");
      }
    else
      {
		print $self -> header;
      }
      
    my $admin_access = $self->getSessionParam('is_admin');
	my $user_access = $self->getSessionParam('user_login');
	my $rights = $self->getSessionParam('rights');

	

    print $self->start_html(
              -title  => "$title",
              -meta   => {'keywords'=>'pangenome,core-genome,accessory,synteny,PAV,comparative genomics,bacteria','description'=> 'PanExplorer is a web-based tool for the analysis and management of pangenome data, through several modules facilitating the exploration of gene clusters and interpretation of data (PAV matrix, phylogeny, synteny)'},
              -class  => 'section-'.$section,
              -script => [
{'-language'=>'javascript', '-src'=>"https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"},
              ]
		   );
	my $call2 = qq~
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.0/css/bootstrap.min.css">
  <!--<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>-->
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>
<script src="//code.jquery.com/jquery-1.11.2.min.js"></script>
  <script src="$Configuration::WEB_DIR/javascript/functions.js"></script>
  <script src="$Configuration::WEB_DIR/javascript/EasyAutocomplete-1.3.5/jquery.easy-autocomplete.min.js"></script>
<link rel="stylesheet" href="$Configuration::WEB_DIR/javascript/EasyAutocomplete-1.3.5/easy-autocomplete.min.css">
<link rel="stylesheet" href="$Configuration::WEB_DIR/javascript/EasyAutocomplete-1.3.5/easy-autocomplete.themes.min.css"> 
  <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.0/js/bootstrap.min.js"></script>~;
	print $call2;
	if ($0 =~/search.cgi/ or $0 =~/synteny.cgi/ or $0 =~/circos.cgi/ or $0 =~/clusters.cgi/){
		print "<script src=\"$Configuration::WEB_DIR/javascript/ajax.js\"></script>";
	}
	my $login_status = "";

	print "<div class=\"container\">";

  }



  
#############################################################################################################################################################
#
#                                                                  end HTML
#
#############################################################################################################################################################

=pod

=head2 endHTML

B<Description>       : displays the base of the web page with genopole logos

B<ArgsCount>         : 0

B<Return>            : void

B<Exception>         :

=cut

sub endHTML
  {
    my $self=shift;
	
    print "<br /></td></tr></table>\n";
	
	my $google_analytics = qq~
	<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-50074693-1', 'cirad.fr');
  ga('send', 'pageview');

</script>\n~;
	#print $google_analytics;
	#
	#
	my $footer = qq~<hr>
      <footer>~;
	print $footer;

    
    print "<table style=\"border-top : 0px solid black;\" width=\"100%\" border=\"0\" cellspacing=\"0\" cellpadding=\"0\"><tr>\n";
    print "<td valign=\"center\" align=\"left\" width=\"19%\"><a href='http://www.southgreen.fr' target=_blank><img src='$Configuration::IMAGES_DIR/logo_southgreen.png' height='35' alt=\"southgreen\" name=\"logo_supagro\" id=\"logo_southgreen\"></a></td>\n";
    print "<td valign=\"center\" align=\"right\" width=\"10%\"><a href='http://www.cirad.fr/' target=_blank><img src='$Configuration::IMAGES_DIR/logo_cirad.gif' height='30' name=\"logo_cirad\" id=\"logo_cirad\"></a>&nbsp;&nbsp;&nbsp;&nbsp;\n";
    print "<a href='http://www.ird.fr/' target=_blank><img src='$Configuration::IMAGES_DIR/logo_ird.gif.jpg' height='30' alt=\"IRD\" name=\"logo_ird\" id=\"logo_ird\"></a>&nbsp;&nbsp;&nbsp;&nbsp;\n";
	#print "<td height='73'></td>\n";
	
	print "<a href='http://www.inra.fr' target=_blank><img src='$Configuration::IMAGES_DIR/LogoINRA-Couleur.jpg' height='30' alt=\"INRA\" name=\"logo_inra\" id=\"logo_inra\"></a></td>\n";
	
	print "</tr></table>\n";
	
    print "</div>\n";
    print $self -> end_html();
  }
  
#############################################################################################################################################################
#
#                                                                  getSession
#
#############################################################################################################################################################

=pod

=head2 getSession

B<Description>       : create a new session if doesn't exist, and return the session id

B<ArgsCount>         : 0

B<Return>            : String

B<Exception>         :

=cut

sub getSession()
  {
    my $self = shift;
#    my $sessionId;
#    if( ! defined( $self -> param('session')))
#      {
#		my $session = new CGI::Session("driver:File", $sessionId, {Directory=>'/tmp'});
#		$sessionId = $session -> id();
#		$session -> delete();
#      }
#    else
#      {
#		$sessionId = $self -> param('session');
#      }
#    return $sessionId;
    return $self->{SESSION};
  }
  

#############################################################################################################################################################
#
#                                                                  clearPreviousAnalysis
#
#############################################################################################################################################################

=pod

=head2 clearPreviousAnalysis

B<Description>       : clear previous analysis results, remove all files of execution directory

B<ArgsCount>         : 0

B<Return>            : void

B<Exception>         :

=cut

sub clearPreviousAnalysis()
  {
    my $self = shift;
    my $session = $self -> getSession();
    my $execution_dir = "$Configuration::IGS_EXECUTION_DIR/".$self -> getSession();
    unlink("out.ps");
    unlink("out.svg");
    unlink("out.pdf");
    unlink("out.tgf");
    unlink("intree");
    unlink("outtree");
    if (-d $execution_dir)
     {
     	open(LS,"ls $execution_dir |");
     	while(<LS>)
     	{
     		if ($_!~/tracability\.hash/ && $_!~/num/ && $_=~ /(.+)/)
     		{
     			my $file = $1;
     			unlink("$execution_dir/$file");
     		}
     	}
     	close(LS);
     	
     	if (-e "$Configuration::TREEDYN_EXE_PATH/guide_tree_edition/$session.current_tree.nwk"){unlink("/home/igs/tools/TreeDyn/guide_tree_edition/$session.current_tree.nwk");}
        if (-e "$Configuration::TREEDYN_EXE_PATH/guide_tree_edition/$session.current_tree.nwk.compute"){unlink("$Configuration::TREEDYN_EXE_PATH/guide_tree_edition/$session.current_tree.nwk.compute");}
        if (-e "$Configuration::TREEDYN_EXE_PATH/guide_tree_edition/$session.script.tds"){unlink("$Configuration::TREEDYN_EXE_PATH/guide_tree_edition/$session.script.tds");}
        if (-e "$Configuration::TREEDYN_EXE_PATH/guide_tree_edition/$session.annotation.tlf"){unlink("$Configuration::TREEDYN_EXE_PATH/guide_tree_edition/$session.annotation.tlf");}
        if (-e "$Configuration::TREEDYN_EXE_PATH/guide_tree_edition/$session.correspondence.hash"){unlink("$Configuration::TREEDYN_EXE_PATH/guide_tree_edition/$session.correspondence.hash");}
       
     }
  }
  
=pod

=head2 getSessionParam

B<Description>:
returns the value of selected session parameter.

B<ArgsCount>: 1

=over 4

=item $param: (string) R

the parameter name.

=back

B<Return>: (string)

the parameter value.

=cut

sub getSessionParam
{
    my ($self, $param) = @_;

    # check parameters
    if (2 != @_)
    {
        confess "usage: my \$value = \$base_cgi->getSessionParam(parameter_name);";
    }

    my $value;
    if ($self->{SESSION} && $param)
    {
        $value = $self->{SESSION}->param($param);
    }
    return $value;
}


=pod

=head1 AUTHORS

Alexis DEREEPER (INRA), alexis.dereeper@supagro.inra.fr

=head1 VERSION

Version 0.1

=head1 SEE ALSO

=cut

return 1; # package return
