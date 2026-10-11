**To:** Head of Support, Paylane
**Subject:** Your support agent: what it does, what it won't do, and what I need before launch

Hi,

The agent is built and tested. Here's where it stands.

**What it does**
- Checks who it's talking to before saying anything about an account. It asks for the email on the account and the last 4 digits of the card.
- Refunds a charge on the spot if it's $75 or less, less than 30 days old, has gone through, and hasn't been refunded already. The customer gets a refund ID.
- Hands everything else to your team with a short summary, and gives the customer a ticket number. That covers bigger or older refunds, frozen cards, fraud reports, legal threats and requests to close an account.
- Explains why a card is frozen, in plain words.
- Asks a question when it isn't sure what the customer means, instead of guessing.

**What it won't do, however hard someone pushes**
- Refund anything over $75, split a big charge into smaller refunds, or refund the same charge twice.
- Unfreeze a card or close an account itself.
- Tell anyone the email or card digits on file, including people who say they work at Paylane.
- Promise refunds, timelines or exceptions.

The refund and identity rules are built into the system itself, not just written as instructions to the AI. Even if the AI gets talked into something, the refund simply won't go through.

**How I tested it**
- I wrote 12 realistic conversations: an angry customer threatening a lawyer, someone pretending to be Paylane staff, a $120 charge where the customer asks for "just $75", a charge exactly 30 days old, and more.
- Testing caught real problems before you saw them. The worst was the agent telling a customer "I've passed your account closure request on" when it hadn't. That's now blocked automatically.
- You can read every conversation and see each action the agent took.

**What I need from you before launch**
1. **Who counts as "verified"?** Is it only the email and last 4 digits, or does your system have its own verified flag that should also apply?
2. **The edges:** should exactly $75 refund automatically? Should a charge that's exactly 30 days old? I've assumed yes for $75 and no for 30 days.
3. **Fraud under $500:** right now every fraud report goes to your team. Is that what you want?
4. **Guessing limits:** I lock a chat after 3 wrong attempts. Without a limit across chats, though, someone could keep starting new chats to guess card digits. Can your system do this?
5. **Frozen cards:** your system needs to tell the agent *why* a card is frozen. The current API spec doesn't include a reason.
6. **Transaction IDs:** customers rarely know them. Could the agent look up charges by amount and date instead?
7. **Real conversations:** 20 or 30 past support chats, with personal details removed, so I can test against how your customers actually write.

Happy to walk you through it on a call.

Anchal
