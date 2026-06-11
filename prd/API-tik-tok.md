Campaign GMV Max
/campaign/gmv_max/create/ (POST): Tạo campaign GMV Max Product/Live (budget, ROAS, ALL/CUSTOMIZED products, schedule…)
  → ZZP: POST /tiktok-business/gmv-max/campaigns

/gmv_max/campaign/get/ (GET): Danh sách campaign GMV Max trong ad account
  → ZZP: GET /tiktok-business/gmv-max/campaigns

/campaign/gmv_max/info/ (GET): Chi tiết 1 campaign GMV Max (cấu hình, trạng thái)
  → ZZP: GET /tiktok-business/gmv-max/campaigns/detail

/campaign/gmv_max/update/ (POST): Cập nhật campaign (budget, roas_bid, promotion_days…); KHÔNG dùng để bật/tắt/xóa
  → ZZP: PUT /tiktok-business/gmv-max/campaigns

/campaign/status/update/ (POST): Bật / tắt / xóa campaign (operation_status: ENABLE | DISABLE | DELETE) — xóa GMV Max campaign dùng API này
  → ZZP: POST /tiktok-business/gmv-max/campaigns/status

Sản phẩm shop (chuẩn bị campaign)
/store/product/get/(GET): Danh sách sản phẩm trong TikTok Shop (SPU/item_group) — dùng khi CUSTOMIZED_PRODUCTS
  → ZZP: GET /tiktok-business/gmv-max/store/products
  → Scope: Onsite Commerce Store (token phải có scope này)

Creative / Video (Product GMV Max)
/gmv_max/video/get/ (GET): Danh sách video/post TikTok khả dụng cho GMV Max campaign của shop
  → ZZP: GET /tiktok-business/gmv-max/videos

/campaign/gmv_max/creative/update/ (POST): Thêm (ADD) hoặc gỡ (REMOVE) video khỏi campaign — inject video KOC sang campaign Hero
  → ZZP: POST /tiktok-business/gmv-max/campaigns/creatives

/gmv_max/creation/custom_anchor_video_list/create/ (POST): Tạo shop-level customized post (gắn video ↔ sản phẩm ở cấp shop)
  → ZZP: POST /tiktok-business/gmv-max/custom-anchor-videos

/gmv_max/creation/custom_anchor_video_list/get/ (GET): Danh sách customized posts (shop/campaign level)
  → ZZP: GET /tiktok-business/gmv-max/custom-anchor-videos

/gmv_max/creation/custom_anchor_video_list/delete/ (POST): Xóa customized posts
  → ZZP: DELETE /tiktok-business/gmv-max/custom-anchor-videos

/gmv_max/creation/shop_video/video_anchors/ (GET): Chi tiết liên kết sản phẩm của video trong customized post
  → ZZP: GET /tiktok-business/gmv-max/shop-video/anchors

Max delivery & Creative boost (trong campaign)
/campaign/gmv_max/session/create/ (POST): Tạo session max delivery (sản phẩm) hoặc creative boost (video)
  → ZZP: POST /tiktok-business/gmv-max/sessions

/campaign/gmv_max/session/update/ (POST): Cập nhật session đang chạy
  → ZZP: PUT /tiktok-business/gmv-max/sessions

/campaign/gmv_max/session/list/ (GET): Danh sách session active trong campaign
  → ZZP: GET /tiktok-business/gmv-max/sessions

/campaign/gmv_max/session/get/ (GET): Chi tiết session theo session_ids
  → ZZP: GET /tiktok-business/gmv-max/sessions/detail

/campaign/gmv_max/session/delete/ (POST): Xóa session
  → ZZP: DELETE /tiktok-business/gmv-max/sessions

Báo cáo hiệu suất
/gmv_max/report/get/ (GET): Báo cáo GMV Max — metrics (cost, gross_revenue, orders, roi…) × dimensions (campaign_id, stat_time_day, item_group_id, item_id…)
  → ZZP: GET /tiktok-business/gmv-max/reports
  → Scope: Reporting > GMV MAX Report