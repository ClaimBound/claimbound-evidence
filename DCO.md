# Developer Certificate of Origin

ClaimBound uses the Developer Certificate of Origin (DCO) 1.1 for contributions.

By making a contribution to this project, I certify that:

1. The contribution was created in whole or in part by me and I have the right to submit it under the open source license indicated in the file; or
2. The contribution is based upon previous work that, to the best of my knowledge, is covered under an appropriate open source license and I have the right under that license to submit that work with modifications under the same license; or
3. The contribution was provided directly to me by another person who certified (1) or (2), and I have not modified it.

I understand that this project and the contribution are public and that a record of the contribution, including the sign-off, may be maintained and redistributed consistent with the project and its license.

## Sign-off

Every commit submitted to ClaimBound must contain a `Signed-off-by:` trailer matching the commit author.

Use:

```bash
git commit -s
```

or add the trailer manually:

```
Signed-off-by: Your Name <your-email@example.com>
```

Pull requests include an automated DCO status check. Commits without a valid sign-off cannot satisfy the DCO check.

Exception: commits authored by Dependabot (`49699333+dependabot[bot]@users.noreply.github.com`) in pull requests opened by `dependabot[bot]` are exempt, because an automated dependency bot cannot certify the DCO. Any other commit pushed to such a pull request still needs a sign-off. Dependency updates are reviewed by the maintainer before merge.
