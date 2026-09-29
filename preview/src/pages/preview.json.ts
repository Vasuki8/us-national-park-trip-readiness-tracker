import { bundle } from '../lib/bundle';
export function GET(){
  const metadata={purpose:bundle.purpose,bundle_id:bundle.bundle_id,data_kind:bundle.data_kind,publication_performed:false,
    parks:bundle.views.map(({snapshot,history})=>({park_code:snapshot.park_code,head_observation_id:history.head_observation_id,
      collection_status:snapshot.collection_status,last_checked_at:snapshot.last_checked_at,last_successful_fetch_at:snapshot.last_successful_fetch_at}))};
  return new Response(JSON.stringify(metadata),{headers:{'Content-Type':'application/json','X-Robots-Tag':'noindex, nofollow'}});
}
