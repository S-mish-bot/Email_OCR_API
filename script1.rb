require 'sidekiq-scheduler'

class OcrApi
    include Sidekiq::Worker
    def perform
        puts "Hii"
        result = `python3 app.py params`
    end
end