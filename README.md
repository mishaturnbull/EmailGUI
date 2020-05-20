# EmailGUI

An inverse spambot!  Most people use spambots to send one email to thousands of
people, whereas this one sends thousands of emails to one person.  As far as I know,
it's A. the only bot like this and B. the only open-source one.

# Dislaimer

THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

## Usage

Allows users to send people a theoretically unlimited amount of emails in one
sitting.  There are limitations, but there are also workarounds.  

### Basic

`$ python EmailGUI.py` gives you a graphical interface that has been tested on
Windows, macOS, and Linux.  It should in theory work on any platform that
supports Python's Tkinter library.

Type in your message, or just use the default, then hit Email, and Send!   If you
realize halfway through that your server is about to die/already dead, there is
an abort mechanism to stop the process early.

### Advanced

Advanced configuration options are described in more detail in the documentation
(link below), and include features such as attempting sender forgery, etc to test
spam filters and the like.

[Click here][config] for a bunch more configuration options.

[config]: https://mishaturnbull.github.io/EmailGUI/configuration.html
