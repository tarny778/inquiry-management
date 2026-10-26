2026/1026/1817
codex意見
25s間作業しました



調査報告
調査対象のルートは /Users/yukinon/Documents/inquiry-management です。コードと設計資料を読み合わせましたが、今回はテスト・ビルドを実行せず、ファイルも変更していません。したがって、以下の評価はソース上の実装内容に基づくもので、実行時の動作を確認したものではありません。
1. アプリ全体の構成と主要ファイル
ファイル・フォルダ	役割
[main.py](/Users/yukinon/Documents/inquiry-management/main.py)	FastAPIアプリ、CORS設定、認証済みユーザー取得、各ルーターの登録
[routers/inquiries.py](/Users/yukinon/Documents/inquiry-management/routers/inquiries.py)	問い合わせの登録・引き受け・完了・再開・検索・詳細取得、調査との関連付け
[routers/investigations.py](/Users/yukinon/Documents/inquiry-management/routers/investigations.py)	調査の検索・詳細・編集・断念・リアクション要求、問い合わせ調査の断念・OK/NG回答
[routers/auth.py](/Users/yukinon/Documents/inquiry-management/routers/auth.py)	ログイン、ログアウト、セッション認証
[schemas/](/Users/yukinon/Documents/inquiry-management/schemas)	FastAPIの入力データ型・検証。問い合わせ、調査編集、認証のスキーマ
[sql/](/Users/yukinon/Documents/inquiry-management/sql)	テーブル定義、認証テーブル追加SQL、業務フロー別のSQLスクリプト
[test/](/Users/yukinon/Documents/inquiry-management/test)	問い合わせ・調査・認証のAPIテスト
[docs/](/Users/yukinon/Documents/inquiry-management/docs)	要件、状態遷移、DB、画面、APIの設計資料
[frontend/src/App.tsx](/Users/yukinon/Documents/inquiry-management/frontend/src/App.tsx)	Reactアプリの画面状態、認証、一覧取得、操作ハンドラー
[frontend/src/api/](/Users/yukinon/Documents/inquiry-management/frontend/src/api)	バックエンドAPI呼び出し
[frontend/src/components/](/Users/yukinon/Documents/inquiry-management/frontend/src/components)	問い合わせ・調査画面のコンポーネント
[frontend/src/types.ts](/Users/yukinon/Documents/inquiry-management/frontend/src/types.ts)	フロントエンドのデータ型
[frontend/package.json](/Users/yukinon/Documents/inquiry-management/frontend/package.json)	Vite、React、TypeScriptなどの依存関係とビルド・lintスクリプト
[requirements.txt](/Users/yukinon/Documents/inquiry-management/requirements.txt)	Python側の依存関係


確認できた事実： バックエンドはFastAPIとPostgreSQL接続（psycopg）、フロントエンドはReact・TypeScript・Viteで構成されています。DBスキーマは日本語名のテーブル・列を使っています。
資料上の全体像： docs/01_要件定義.md は問い合わせ全体、調査、問い合わせと調査の関係を分けて管理する方針です。docs/02_業務フロー・状態遷移.md と docs/03_データベース設計.md が業務状態とデータ構造、docs/04_画面設計.md が画面、docs/05_API設計.md がAPI仕様を説明しています。
2. 実装済みの機能と未実装の機能
実装を確認できた機能
ルーターの定義とフロントエンドのAPI呼び出しから、次の機能が実装されています。
- 職員番号とパスワードによるログイン、ログアウト、現在のセッション確認
- 問い合わせの登録、更新、一覧検索、詳細取得
- 問い合わせの個別・一括引き受け、個別・一括対応完了、対応再開
- 問い合わせへの調査新規作成・関連付け、既存調査への個別・一括関連付け
- 調査の一覧検索、詳細取得、編集、断念、リアクション要求
- 問い合わせ調査ごとの個別断念、OK回答、NG回答と移行先への関連付け
- フロントエンドでの問い合わせ一覧・詳細・登録・編集と、調査一覧・詳細・編集
確認したファイル： routers/inquiries.py、routers/investigations.py、routers/auth.py、frontend/src/App.tsx、frontend/src/api/*.ts、frontend/src/components/。
未実装、または実装を確認できない機能
- 対応担当者変更API・変更履歴の閲覧画面は確認できません。DB定義には 対応担当者変更履歴 テーブルがありますが、ルーターにもフロントエンドにも対応する機能が見当たりません。
- Docker化、CI/CD、AWSデプロイは、要件資料では開発工程として挙げられていますが、このリポジトリのファイル一覧から実装を確認できません。
- 将来拡張として記載されたFAQ整理支援などは、実装を確認できません。
- 初期スクリプトにあるSQLテストは存在しますが、実行結果は今回確認していません。
「未実装」は、今回確認したリポジトリ内に該当する実装を見つけられなかったという意味です。別環境や別ブランチに存在するかは未確認です。
3. 設計資料と実装の不一致、確認が必要な点
1. 問い合わせ再開の仕様とDB設計が一致していません。
   API設計書 docs/05_API設計.md には、完了後7日以内の再開APIが記載され、routers/inquiries.py にも再開処理があります。一方、docs/03_データベース設計.md は再開の詳細仕様を今後検討するとし、SQLテスト対象からも除外しています。再開後に既存の問い合わせ調査をどう扱うか、設計を確定する必要があります。
2. 対応担当者変更履歴はDBに定義されていますが、変更機能が見当たりません。
   docs/03_データベース設計.md と sql/01_create_tables.sql に履歴テーブルがあり、docs/04_画面設計.md には画面103があります。しかし、変更API・履歴取得API・対応画面を確認できません。設計上の予定機能なのか、実装漏れなのか確認が必要です。
3. 初期表示条件が設計書間で異なります。
   問い合わせ一覧は docs/04_画面設計.md とAPI設計で利用者区分に応じた初期表示が定義されています。調査一覧も画面設計では一般職員・情シス職員別の初期条件がありますが、docs/05_API設計.md のAPI21は「ログイン職員に基づく検索制限をしない」としています。画面側が条件を常に設定する前提なのか、実際に意図した一覧になるのか、確認が必要です。
4. 画面設計にある機能のうち、画面実装を確認できないものがあります。
   対応担当者変更履歴の画面103は前述のとおり確認できません。また、画面設計の調査一覧は20件表示とありますが、フロントエンドのAPI呼び出しは page_size=50 を指定しています（frontend/src/api/investigations.ts）。
5. 認証CookieのSecure設定は設計書の記載と環境設定に依存します。
   docs/05_API設計.md はCookieの Secure=true を仕様としています。routers/auth.py は ENVIRONMENT=production の場合だけ secure=True にします。開発環境でSecure属性が付かない点は想定どおりと思われますが、本番環境の起動設定が未確認なので、本番での一致は確認できていません。
6. DB初期化SQLの適用方法を整理する必要があります。
   sql/01_create_tables.sql は既存テーブルを削除して作り直すDDLで、業務テーブルに加えて認証テーブルも含みます。一方、sql/99_認証用テーブルの追加.sql は認証テーブルのみを追加します。新規構築・既存DB更新でどちらを適用するのか、実DBの状態も含めて確認が必要です。なお、今回はSQLを実行していません。
7. 時刻の扱いを再確認してください。
   routers/auth.py のセッション時刻はUTC付きで扱う一方、問い合わせ・調査処理の多くは datetime.now() を使い、DDLは業務日時に TIMESTAMP、認証日時に TIMESTAMPTZ を使っています。タイムゾーン変換や比較が一貫しているかは、実DB・稼働環境を含めて未確認です。
4. バックエンドテストとフロントエンドビルドの状況
テスト・ビルドは実行していません。 今回の依頼が読み取り専用の調査であるため、テストやビルドの成否は報告できません。実行済みとは扱っていません。
ソース上では、バックエンドテストは test/test_inquiries.py、test/test_investigations.py、test/test_auth.py にあります。正常系・異常系の多数のテスト関数とfixtureが定義されています。requirements.txt にはpytest関連依存が記載されています。
フロントエンドの frontend/package.json には次のスクリプトがあります。
- build: tsc -b && vite build
- lint: eslint .
推測： テストfixtureはPostgreSQLに接続してテーブルやデータを操作する構成に見えますが、テスト実行環境・DB接続先・fixtureの実際の影響範囲は、今回テストを実行していないため確認できていません。
5. 開発再開前に優先して確認すべき事項
1. 実行環境とDBの確認： 使用するDB名、接続設定、現在のスキーマ、01_create_tables.sql と 99_認証用テーブルの追加.sql の適用方針を確認する。
2. 仕様の確定： 問い合わせ再開の状態・期限・関連調査の扱いと、対応担当者変更履歴を実装対象に含めるか決め、設計書間の差を解消する。
3. 権限と初期一覧条件： 問い合わせ・調査の各一覧について、一般職員と情シス職員それぞれがどの範囲を見られるべきか、設計と画面/APIの責任分界を確認する。
4. テスト環境の安全性： バックエンドテストが接続するDBを特定し、開発用・テスト用DBが本番や共有DBと分離されていることを確かめてから実行する。
5. 環境設定と時刻： 本番CookieのSecure属性、CORS許可先、バックエンドとDBのタイムゾーンを確認する。
6. 検証の実行： 上記確認後に、バックエンドテストとフロントエンドのビルドを実行して結果を記録する。
調査時の作業ツリー状態
読み取り専用の確認のみを行いました。調査開始時の git status --short では docs/気づき.md に変更が表示されていました。これは調査前から存在する変更として扱い、内容を変更していません。

17:56

gpt意見
おすすめの進め方

第1段階：画面デザインを仕上げる
まずは現在のフロントエンドを使いやすく整える。
- 一覧・詳細・新規登録・編集画面のデザインを調整
- 問い合わせ画面と、今後作る問題調査画面の構成を整理
- エラー表示、ダイアログ、ボタン、余白などの統一
- 画面を操作して、既存機能が壊れていないことを確認
ここでは原則として、APIの仕様や業務ルールを不用意に変更しない。




第2段階：設計書と実装の不一致を解消する
Codexの監査結果を出発点に、実装・テスト・設計書を突き合わせる。
- API設計書と実際のAPIの入出力、権限、エラー処理
- 画面設計書と実際の画面・操作
- DB設計書とテーブル定義
- ページ件数、初期表示条件、検索条件などの差異
- 未実装機能と、単なる記載漏れの区別
ここは、単に設計書を直す作業ではないよ。実装が意図した仕様を満たしているか判断し、必要なら実装も修正する。その後にテストを実施して、設計書を現状に合わせる。

成果物：実装・テスト・設計書の整合が取れた状態。




第3段階：将来拡張を取捨選択する
当初、後回しにしていた機能について、実装する価値と費用を考える。
- 担当者変更履歴管理
- メール通知
- FAQ整理支援
それぞれについて、業務上の必要性、実装の難易度、デプロイ後の運用負担、ポートフォリオとしての学習効果を見て決めよう。

全部実装する必要はない。実装しないと決めた機能は、未実装であることと、その判断理由を整理しておけばよい。




第4段階：時刻と認証の扱いを整理する
Codexの指摘のうち、時刻の扱いは、デプロイの準備に入る前に確認したい。

時刻の扱い
- Pythonの日時取得、DB列の型、日時の比較・検索を調査
- 日本時間で表示すべき業務日時と、セッション期限などの時刻を整理
- 必要な修正を行い、テストで確認
認証Cookie
- 開発環境と本番環境の設定を明確にする
- 本番で ENVIRONMENT=production が確実に設定される仕組みを決める
- HTTPSで Secure 属性が有効になることを検証する
この段階では、現状調査を先に行い、問題が確認された箇所だけを修正する。




第5段階：Docker化・CI/CD・AWSデプロイ
ここは、ゆきのんがぜひ学びたいと言っている重要な工程だね。単にファイルを追加するのではなく、開発から公開までを自分で説明できる状態を目指そう。
1. Docker化：FastAPI、React、PostgreSQLの構成と起動方法を整理する。
2. CI/CD：GitHubへのプッシュやプルリクエストを契機に、テストやビルドを自動実行する。
3. AWSデプロイ：アプリを公開し、環境変数、DB接続、HTTPS、認証Cookieを本番環境で検証する。
4. 運用確認：ログ、エラー時の確認方法、バックアップや復旧方法など、公開後に必要なことを整理する。
ここは一度に全部やらず、Docker、CI/CD、AWSの順に、仕組みを理解しながら進めるのがよいと思う。

