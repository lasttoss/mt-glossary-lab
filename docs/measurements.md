# Measurements

Machine: Ryzen 7 8845HS, 32 GB RAM, Ubuntu 24.04, CPU only, int8, 8 threads, beam 2.
Model: VietAI envit5 (T5, 266M) converted to CTranslate2, directory `envit5-ct2`.

## `python -m mtgloss eval --set all --verbose`

```
  [ok  ] deploy+production        | Tối nay chúng ta sẽ deploy xây dựng mới để production.
          model alone missed it: 'We will deploy the new build to production tonight'
  [ok  ] server                   | server lại hết bộ nhớ lúc nửa đêm.
          model alone missed it: 'The server ran out of memory again at midnight'
  [ok  ] pull request+review      | Vui lòng mở pull request và yêu cầu review
          model alone missed it: 'Please open a pull request and ask for a review'
  [ok  ] migrate                  | Bạn có khả năng migrate bảng người dùng tới cụm mới không?
          model alone missed it: 'Can you migrate the users table to the new cluster'
  [ok  ] database+query           | database query mất 400 mili giây.
          model alone missed it: 'The database query takes 400 milliseconds'
  [ok  ] release                  | Chúng ta cần hoãn việc release vào thứ sáu.
          model alone missed it: 'We need to roll back the release on Friday'
  [ok  ] debug                    | Thêm bản ghi debug trước khi thử lại.
          model alone missed it: 'Add a debug log before the retry'
  [ok  ] branch                   | branch này ở phía sau chính, kéo đầu tiên.
          model alone missed it: 'The branch is behind main, pull first'
  [ok  ] test                     | Chạy test trước khi bạn hợp nhất trước.
          model alone missed it: 'Run the test suite before you merge'
  [ok  ] deploy                   | Độ trễ tăng lên sau lần deploy cuối
          model alone missed it: 'The latency went up after the last deploy'
  [ok  ] server                   | server của chúng tôi cần thêm CPU trong giờ cao điểm.
          model alone missed it: 'Our server needs more CPU during peak hours'
  [ok  ] pull request+review      | Anh có thể review pull request của tôi trước khi ăn trưa không?
          model alone missed it: 'Can you review my pull request before lunch'
  [MISS] migrate+database         | Cuối tuần trước chúng tôi đã migrate vào rồi.
          model alone missed it: 'We migrated the database last weekend'
  [ok  ] server+production        | server production lại khỏe mạnh trở lại.
          model alone missed it: 'The production server is healthy again'
dev      cases 14 · model alone  0/14 · + term table 13/14 · p50 151 ms · p95 230 ms
  [ok  ] deploy                   | Vui lòng deploy Hotfix sau khi đứng lên.
          model alone missed it: 'Please deploy the hotfix after the standup'
  [ok  ] database                 | database chỉ được đọc trong cửa sổ dịch chuyển.
          model alone missed it: 'The database is read-only during the migration window'
  [ok  ] server                   | server của chúng tôi trả về 500 lỗi trong khi nạp.
          model alone missed it: 'Our server returns 500 errors under load'
  [ok  ] branch+pull request      | Đẩy branch của bạn và mở pull request (remix).
          model alone missed it: 'Push your branch and open a pull request'
  [ok  ] debug                    | Chúng tôi debug cho khách hàng xếp hàng mỗi đêm.
          model alone missed it: 'We debug the queue consumer every night'
  [ok  ] release                  | Các ghi chú release là thiếu bước quay trở lại.
          model alone missed it: 'The release notes are missing the rollback step'
  [MISS] review+query             | Rà soát kế hoạch query trước khi thay đổi chỉ mục.
          model alone missed it: 'Review the query plan before you change the index'
  [ok  ] migrate                  | migrate các khúc gỗ cũ đến kho lạnh để lưu trữ.
          model alone missed it: 'Migrate the old logs to cold storage'
holdout  cases  8 · model alone  0/8 · + term table  7/8 · p50 151 ms · p95 166 ms
misses: 2/22  (a term table cannot restore words the model dropped — see docs/measurements.md)
```

## What the two misses look like

```
We migrated the database last weekend
  model: Cuối tuần trước chúng tôi đã chuyển dữ liệu vào rồi.
  -> the noun "database" is gone, not mistranslated; no rule can put it back

Review the query plan before you change the index
  model: Rà soát kế hoạch query trước khi thay đổi chỉ mục.
  -> "Rà soát" is a correct paraphrase of review, so the table never fires
```

## Reproduce

```bash
python -m pytest -q
python -m mtgloss eval --model-dir /path/to/envit5-ct2 --set all --verbose
```
