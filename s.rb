require 'google/apis/gmail_v1'
require 'googleauth'
require 'googleauth/stores/file_token_store'
require 'fileutils'
require 'json'
require 'zip'
require 'aws-sdk-s3'


# require 'sidekiq-scheduler'

SERVICE = Google::Apis::GmailV1::GmailService.new
SERVICE.client_options.application_name = 'InboxChecker'


GMAIL_QUERY = "label:UNREAD has:attachment to:marialois836@gmail.com"
OOB_URI = "urn:ietf:wg:oauth:2.0:oob".freeze
APPLICATION_NAME = "Gmail API Ruby Quickstart".freeze
CREDENTIALS_PATH = "client-secret.json".freeze
TOKEN_PATH = "token.yaml".freeze

SCOPE = Google::Apis::GmailV1::AUTH_GMAIL_MODIFY



# class GmailApi
#   include Sidekiq::Worker

  def authorize
      puts("inside authorize")
      client_id = Google::Auth::ClientId.from_file CREDENTIALS_PATH
      token_store = Google::Auth::Stores::FileTokenStore.new file: TOKEN_PATH
      authorizer = Google::Auth::UserAuthorizer.new client_id, SCOPE, token_store
      user_id = "default"
      credentials = authorizer.get_credentials user_id

      if credentials.nil?
        url = authorizer.get_authorization_url base_url: OOB_URI
        puts "Open the following URL in the browser and enter the " \
            "resulting code after authorization:\n" + url
        code = gets
        credentials = authorizer.get_and_store_credentials_from_code(
          user_id: user_id, code: code, base_url: OOB_URI
        )
      end
      credentials
  end
    

  def read_email_attachments
    user_id = 'me'
    
    SERVICE.list_user_labels(user_id).labels.each do |label|
      if label.name == 'UNREAD' then
        emails_received  = SERVICE.list_user_messages(user_id, q: GMAIL_QUERY)
        
        emails_received.messages.each do |i|
          
          msg_id = i.id
          email = SERVICE.get_user_message(user_id, msg_id)
          email.payload.parts.each.find do |part|
       
          if(part.mime_type=='application/pdf')
            attachment_id = part.body.attachment_id
       
          email_message = SERVICE.get_user_message_attachment(user_id, msg_id, attachment_id)
          file_name = "Invoice_#{Time.now.strftime('%Y%m%d%H%M%S%12N')}.pdf"
          File.open(file_name, 'wb') {|f| f.puts (email_message.data)}
          
          puts "File attached"
          end
        end
          SERVICE.modify_message(user_id, msg_id, body={ 'remove_label_ids': ['UNREAD']})
        end
       
      end
    end
  end

  def object_uploaded?(s3_client, bucket_name, object_key, body_file)
    response = s3_client.put_object(
      bucket: bucket_name,
      key: object_key,
      body: body_file
    )
    if response.etag
      return true
    else
      return false
    end
  rescue StandardError => e
    puts "Error uploading object: #{e.message}"
    return false
  end

  def run_me()
    for files in Dir.glob('*.pdf') do
      File.open(files,'rb') do |file|
        puts("inside run me")
        bucket_name = 'gamilapi'
        object_key = files
        body_file = file
            # body_file = name
        region = 'ap-south-1'
        s3_client = Aws::S3::Client.new(region: region)
        
        if object_uploaded?(s3_client, bucket_name, object_key, body_file)
          puts "Object '#{object_key}' uploaded to bucket '#{bucket_name}'."
        else
          puts "Object '#{object_key}' not uploaded to bucket '#{bucket_name}'."
        end
      end
    end
  end

  # def middle1
    SERVICE.authorization = authorize

    puts "Fetching Attachments.."
    read_email_attachments
    puts "Before Run Me"
    # run_me
    
  # end

  # --- main program starts here
#   def perform
#     middle1
#     puts "After File Attached"
#   end
# end

# result = `python3 app.py params`