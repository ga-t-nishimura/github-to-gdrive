## 背景
PR&マーケティング部では、Claude Codeの活用推進を行っています。Claude Codeで開発したアプリはGitHubで管理しますが、部内のメンバーのほとんどはGitHubについて詳しく知らないので
- GitHub: コード、プログラム一式
- Google Drive: マニュアル、人が読むためのドキュメント、GitHubリポジトリURL 等
という管理をしようと考えています。

## やりたいこと
「GitHubリポジトリ <--> Google Driveのフォルダー」という対応表を用意しておくことによって、GitHubリポジトリのmainブランチがpushされた際に、自動的にリポジトリ内のREADME.mdやマニュアルドキュメントを自動的にGoogle Driveのフォルダーに上書き更新する仕組みを作りたい。